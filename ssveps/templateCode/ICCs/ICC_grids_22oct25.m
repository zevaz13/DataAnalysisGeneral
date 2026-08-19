clear all; 

loadFolder = 'C:\Users\zevaz\OneDrive\Escritorio\Metamers\eegExp\results\rawGRIDFBCCA\';
cd(loadFolder)

load('groupData.mat'); % loads cellResults

numSubinDataset = numel(cellResult);

% Sets from the healthy group
healthy = {'MET000' 'MET001' 'MET002' 'MET003' 'MET004' 'MET005' 'MET006' 'MET007' 'MET008' 'MET009' 'MET010'...
           'MET011' 'MET012' 'MET018' 'MET020' 'MET021' 'MET022' 'MET023' 'MET024' 'MET026' 'MET027' };
% Sets from the protan group
protans = {'MET016' 'MET016b' 'MET017' 'MET017b' 'MET028' 'MET031' 'MET035' 'MET036'};
% Sets from the deutan group
deutans = {'MET015'  'MET029' 'MET032' 'MET033' 'MET034'};
others  = {'MET019' 'MET025' 'MET030'};
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

redArray    = cellResult{1}.redArray;
greenArray  = cellResult{1}.greenArray;

% Extract all subIDs from cellResults
allSubIDs = cellfun(@(s) s.subID, cellResult, 'UniformOutput', false);

% Example: allSubIDs = {'MET001', 'MET001y', 'MET002', 'MET003', 'MET003x'};

% Convert to string array for easier manipulation
allSubIDs_str = string(allSubIDs);

% Extract the first 6 characters
prefixes = extractBefore(allSubIDs_str, 7);  % gets 'MET001', 'MET002', etc.

% Find unique prefixes
uniquePrefixes = unique(prefixes);

% Create a map of indices for each shared prefix
sharedIdx = cell(size(uniquePrefixes));
for i = 1:numel(uniquePrefixes)
    sharedIdx{i} = find(prefixes == uniquePrefixes(i));
end

for i = 1:numel(sharedIdx)
    groupIndices = sharedIdx{i};
    groupIDs = allSubIDs(groupIndices);
    
    fprintf('Group %d (prefix: %s):\n', i, allSubIDs{groupIndices(1)}(1:6));
    disp(groupIDs);
end

% Filter sharedIdx to keep only groups with exactly 2 entries
filteredIdx = sharedIdx(cellfun(@numel, sharedIdx) == 2);
filteredIDs = cellfun(@(idx) allSubIDs(idx), filteredIdx, 'UniformOutput', false);

% Convert healthy list to string array for comparison
% Convert healthy list to string array
healthy_str = string(healthy);

% Initialize output
finalIdx = {};

for i = 1:numel(filteredIdx)
    groupIDs = allSubIDs(filteredIdx{i});
    prefix = extractBefore(string(groupIDs(1)), 7);  % first 6 characters
    
    if any(healthy_str == prefix)
        finalIdx{end+1} = filteredIdx{i};  % keep this group
    end
end
finalIDs = cellfun(@(idx) allSubIDs(idx), finalIdx, 'UniformOutput', false);

%% show the names of the only CTR people.
for subi = 1:numel(finalIDs)
    finalIDs{subi}
end

%% show the names of the whole geoup that we have 2 runs for. 
for subi = 1:numel(filteredIDs)
    filteredIDs{subi}
end

%%
[r, LB, UB, F, df1, df2, p] = computeICC_gridMaps(finalIdx, finalIDs,cellResult);
% [r, LB, UB, F, df1, df2, p] = computeICC_gridMaps(filteredIdx, filteredIDs,cellResult);

[rall, LBall, UBall, Fall, df1all, df2all, pall] = computeICC_gridMaps(filteredIdx, filteredIDs,cellResult);


%%
r_reshaped = reshape(r, 10, 10);
meanICC = mean(r_reshaped,'all');

figure;
imagesc(redArray,greenArray, r_reshaped); set(gca,'YDir','normal'); hold on; title(['ICC_3 agreement = ' num2str(meanICC,2)], 'FontSize', 16); hold on;
axis square; clim([0 1]);set(gca,'YDir','normal'); hold on; 
xticks(floor(redArray)); xtickangle(0)
yticks(floor(greenArray))
xlabel('Red LED (D/A units)', 'FontSize', 14); ylabel('Green LED (D/A units)', 'FontSize', 14)
colorbar

r_reshaped_all = reshape(rall, 10, 10);
meanICCall = median(r_reshaped_all,'all');

figure;
imagesc(redArray,greenArray, r_reshaped_all); set(gca,'YDir','normal'); hold on; title(['ICC_3 agreement = ' num2str(meanICCall,2)], 'FontSize', 16); hold on;
axis square; clim([0 1]);set(gca,'YDir','normal'); hold on; 
xticks(floor(redArray)); xtickangle(0)
yticks(floor(greenArray))
xlabel('Red LED (D/A units)', 'FontSize', 14); ylabel('Green LED (D/A units)', 'FontSize', 14)
colorbar

%%
points2use = [0 1111; 2488 222; 3200 1333; 711 1777; 2133 2000]

points2search = [redArray' greenArray']
xvals = points2use(:,1);   % [0; 2488; 3200; 711; 2133]
yvals = points2use(:,2);   % [1111; 222; 1333; 1777; 2000]

idxRed = zeros(size(xvals));

for i = 1:length(xvals)
    [~, idxRed(i)] = min(abs(redArray - xvals(i)));
end

idxGreen = zeros(size(yvals));

for i = 1:length(yvals)
    [~, idxGreen(i)] = min(abs(greenArray - yvals(i)));
end

[redArray(idxRed)' greenArray(idxGreen)']

twoDindex = [idxRed idxGreen];
r(1,6)

ICC5pix = zeros(1,numel(idxGreen));
ICC5pixAll = zeros(1,numel(idxGreen));
for xi = 1:numel(idxGreen)
    ICC5pix(xi) = r_reshaped(idxGreen(xi),idxRed(xi));
    ICC5pixAll(xi) = r_reshaped_all(idxGreen(xi),idxRed(xi));
end

median(ICC5pix)
median(ICC5pixAll)