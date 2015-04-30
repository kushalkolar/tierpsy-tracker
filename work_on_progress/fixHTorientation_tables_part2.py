# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 10:21:02 2015

@author: ajaver
"""

import pandas as pd
import tables
import h5py
import numpy as np
from min_avg_difference import min_avg_difference
#from image_difference import image_difference
import os
import time

import matplotlib.pylab as plt


contrastmap_file = '/Users/ajaver/Desktop/Gecko_compressed/20150323/Trajectories/CaptureTest_90pc_Ch1_02022015_141431_cmap-short.hdf5';
segworm_file = '/Users/ajaver/Desktop/Gecko_compressed/20150323/Trajectories/CaptureTest_90pc_Ch1_02022015_141431_segworm.hdf5';

#contrastmap_fid = h5py.File(contrastmap_file, 'r');

segworm_file_fix = segworm_file[:-5] + '_fix2' + segworm_file[-5:];
os.system('cp "%s" "%s"' % (segworm_file, segworm_file_fix))

cmap_fid = pd.HDFStore(contrastmap_file, 'r');
block_index = cmap_fid['/block_index'];

block_ini = block_index[block_index['block_ini_id']>=0]
block_ini = block_ini.rename(columns={'block_ini_id':'cmap_id'})

block_last = block_index[block_index['block_last_id']>=0]
block_last = block_last.rename(columns={'block_last_id':'cmap_id'})

cmap_fid.close()

contrastmap_fid = tables.File(contrastmap_file, 'r');
segworm_fid = h5py.File(segworm_file_fix, 'r+');
#%%

tic_ini = time.time()
worm_ids = block_index['worm_index_joined'].unique();
for ii_worm, worm_id in enumerate(worm_ids):
    tic = time.time()
    dat_ini = block_ini[block_ini['worm_index_joined']==worm_id]
    block_ids = {};
    cmaps_ids = {};
    
    block_ids['ini'] = dat_ini['block_id'].values
    cmaps_ids['ini'] = dat_ini['cmap_id'].values
    if block_ids['ini'].size == 1:
        continue
    dat_last = block_last[block_last['worm_index_joined']==worm_id]
    block_ids['last'] = dat_last['block_id'].values
    cmaps_ids['last'] = dat_last['cmap_id'].values
    
    
    max_block = np.max([np.max(block_ids['ini']),np.max(block_ids['last'])])
    is_switch = {'H': np.zeros(max_block-1), 'D':np.zeros(max_block-1)}
    
    
    for block_id in range(1,max_block): #it is not necessary to add one to block max
        good_cur  = block_ids['ini'] == block_id+1 
        curr_block_id = cmaps_ids['ini'][good_cur]
        assert np.all(np.diff(curr_block_id)==1)
        curr_range  = (curr_block_id[0], curr_block_id[-1]+1)
        
        
        tot_prev = 0
        ii_add = 0
        prev_rangeS = []
        while tot_prev < 100  and block_id-ii_add >= 0:  
            good_prev = block_ids['last'] == block_id;
            prev_block_id = cmaps_ids['last'][good_prev]
            assert np.all(np.diff(prev_block_id)==1)
            
            prev_rangeS += [(prev_block_id[0], prev_block_id[-1]+1)]
            tot_prev += prev_block_id.size

        
        if len(prev_block_id)<2 or len(curr_block_id)<2:
            continue
        #%%
        
        for n1,n2 in [('H', 'T'), ('D', 'V')]:
            all_min_diff = {}
            for key_prev in [n1,n2]:
                for key_curr in [n1, n2]:
                    for map_type in ['neg', 'pos']:
                        key_map_curr = '/block_ini/worm_%s_%s' % (key_curr, map_type)
                        buff_curr = contrastmap_fid.get_node(key_map_curr)[curr_range[0]:curr_range[1],:,:]                 
                        
                        key_map_prev = '/block_last/worm_%s_%s' % (key_prev, map_type);
                        buff_prev = np.zeros((tot_prev, buff_curr.shape[1], buff_curr.shape[2]), dtype = buff_curr.dtype)
                        tot = 0;
                        for prev_range in prev_rangeS:
                            vv = range(tot, tot + prev_range[1]-prev_range[0]);
                            tot = vv[-1]
                            buff_prev[vv,:,:] = contrastmap_fid.get_node(key_map_prev)[prev_range[0]:prev_range[1],:,:]
                        
                        all_min_diff[key_prev + key_curr + '_' + map_type] = min_avg_difference(buff_prev, buff_curr);       
                        
        
            prob_switch = {}
            for ind in [(n1+n1, n1+n2), (n2+n2, n2+n1)]:
                for map_key in ['_neg', '_pos']:
                    #min_eq = np.min(all_avg_diff[ind[0] + map_key], axis=1);
                    #min_dif = np.min(all_avg_diff[ind[1] + map_key], axis=1)
                    min_eq = all_min_diff[ind[0] + map_key]
                    min_dif = all_min_diff[ind[1] + map_key]
                    prob_switch[ind[0] + map_key] = np.mean(min_dif-min_eq) #this will be negative only if the change is prefered
            is_switch[n1][block_id-1] = np.sum([prob_switch[key] for key in prob_switch])
            
#            plt.figure()
#            
#            plt.subplot(2,2,1)
#            plt.plot(all_min_diff[n1+n1+'_pos'])
#            plt.plot(all_min_diff[n1+n2+'_pos'])
#            
#            plt.subplot(2,2,2)
#            plt.plot(all_min_diff[n2+n2+'_pos'])
#            plt.plot(all_min_diff[n2+n1+'_pos'])
#            
#            plt.subplot(2,2,3)
#            plt.plot(all_min_diff[n1+n1+'_neg'])
#            plt.plot(all_min_diff[n1+n2+'_neg'])
#            
#            plt.subplot(2,2,4)
#            plt.plot(all_min_diff[n2+n2+'_neg'])
#            plt.plot(all_min_diff[n2+n1+'_neg'])
    
    block2switch = {}
    for key in is_switch:
        dum = np.cumprod(np.where(is_switch[key]<0, -1, 1));
        block2switch[key] = np.where(dum==-1)[0]+2;
#%%    
    
    
    for bb in block2switch['H']:
        kernel = '(worm_index_joined==%d) & (block_id==%d)' % (worm_id, bb)
        block_segworm_id = block_index.query(kernel)['segworm_id']
        for cc in ['skeleton', 'contour_dorsal', 'contour_ventral']:
            for nn in block_segworm_id:
                aa = segworm_fid['/segworm_results/' + cc][nn,:,:]
                segworm_fid['/segworm_results/' + cc][nn,:,:] = aa[:,::-1]
    
    for bb in block2switch['D']:
        kernel = '(worm_index_joined==%d) & (block_id==%d)' % (worm_id, bb)
        block_segworm_id = block_index.query(kernel)['segworm_id']
        for nn in block_segworm_id:
            vv = segworm_fid['/segworm_results/contour_ventral'][nn,:,:]
            dd = segworm_fid['/segworm_results/contour_dorsal'][nn,:,:]
            
            segworm_fid['/segworm_results/contour_ventral'][nn,:,:] = dd
            segworm_fid['/segworm_results/contour_dorsal'][nn,:,:] = vv
            
    
    print ii_worm, len(worm_ids), time.time()-tic, time.time()-tic_ini
#%%
segworm_fid.close()
contrastmap_fid.close()




#            tot = 0;
#            for neq in min_eq:
#                tot += np.sum(neq>min_dif)
#            prob_switch[ind[0] + map_key] = tot/float(min_eq.size*min_dif.size)
    
    
#    good = np.min(all_avg_diff['TT_neg'], axis=1)<np.min(all_avg_diff['TH_neg'], axis=1)
#    prob_switch['TT_neg'] = (np.sum(good)/float(good.size));
#
#    good = np.min(all_avg_diff['HH_pos'], axis=1)<np.min(all_avg_diff['HT_pos'], axis=1)
#    prob_switch['HH_pos'] = (np.sum(good)/float(good.size));
#
#    good = np.min(all_avg_diff['TT_pos'], axis=1)<np.min(all_avg_diff['TH_pos'], axis=1)
#    prob_switch['TT_pos'] = (np.sum(good)/float(good.size));
#    print prob_switch
#    
#    import matplotlib.pylab as plt
#    plt.figure()
#    plt.subplot(2, 2, 1)
#    plt.plot(np.min(all_avg_diff['HH_neg'], axis=1), 'g')
#    plt.plot(np.min(all_avg_diff['HT_neg'], axis=1), 'r')
#    plt.title(prob_switch['HH_neg'])
#    
#    plt.subplot(2, 2, 2)
#    plt.plot(np.min(all_avg_diff['TT_neg'], axis=1), 'g')
#    plt.plot(np.min(all_avg_diff['TH_neg'], axis=1), 'r')
#    plt.title(prob_switch['TT_neg'])
#    
#    plt.subplot(2, 2, 3)
#    plt.plot(np.min(all_avg_diff['HH_pos'], axis=1), 'g')
#    plt.plot(np.min(all_avg_diff['HT_pos'], axis=1), 'r')
#    plt.title(prob_switch['HH_pos'])
#    
#    plt.subplot(2, 2, 4)
#    plt.plot(np.min(all_avg_diff['TT_pos'], axis=1), 'g')
#    plt.plot(np.min(all_avg_diff['TH_pos'], axis=1), 'r')
#    plt.title(prob_switch['TT_pos'])


            

#diff_avg_HH[kp, kn] = image_difference(contrastmap_fid['/worm_H_neg'][prev_block[kp],:,:], 
#                    contrastmap_fid['/worm_H_neg'][next_block[kn],:,:])