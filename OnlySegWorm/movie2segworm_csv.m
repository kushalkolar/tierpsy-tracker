function movie2segworm_csv(save_csv_name, masked_image_file, trajectories_file)
%read data from worm trajectories
disp(save_csv_name)
disp(masked_image_file)
disp(trajectories_file)
AA = importdata(save_csv_name);

data = [];
AA.colheaders{1} = 'plate_worms_id';
for ii = 1:numel(AA.colheaders)
    data.(AA.colheaders{ii}) = AA.data(:,ii);
end
clear AA

[~,base_name,~] = fileparts(save_csv_name);
movie2segwormfun(data, masked_image_file, trajectories_file, base_name);