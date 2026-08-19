clear all;

%% This script performs permutation based testing using the SSVEP maps, between the groups. This script aims to find directional differences in the maps.
% instead of only asking whether there is a difference between them, it
% will use the z-scores to get cluster weights.

% where is the data
ssvepPath   = 'C:\Users\zevaz\OneDrive\Escritorio\Metamers\eegExp\SSVEPGRIDdataResults\';

% Sets from the healthy group
% Subs2checkHC = {'MET000' 'MET001' 'MET002' 'MET003' 'MET004' 'MET005b' 'MET006' 'MET007' 'MET008' 'MET009' 'MET010'...
%               'MET011' 'MET012' 'MET018' 'MET020' 'MET021' 'MET022' 'MET023' 'MET024' 'MET026' 'MET027' };
Subs2checkHC = { 'MET000' 'MET001' 'MET002' 'MET003' 'MET004' 'MET005b' 'MET006' 'MET007' 'MET008' 'MET009' 'MET010'...
              'MET011' 'MET012' 'MET018' 'MET020' 'MET021' 'MET022' 'MET023' 'MET024' 'MET026' 'MET027' };

% Sets from the CVD group

Subs2checkCVD = {'MET015' 'MET016' 'MET016b' 'MET017' 'MET017b' 'MET028' 'MET029' 'MET031' 'MET032' 'MET033' 'MET034' 'MET043' 'MET044' 'MET045' 'MET046'};

%% Load and save datasets
numSubHC     = numel(Subs2checkHC); numSubCVD     = numel(Subs2checkCVD);
dataArrayHC  = zeros(10, 10, numSubHC);
dataArrayCVD  = zeros(10, 10, numSubCVD);

% array for Healthy controls
for si =1:numSubHC
    % load the 
    SubID   = Subs2checkHC{si};
    load([ssvepPath SubID '.mat'])
    dataArrayHC(:,:,si) = NormMatrix;
end

% array for CVDs
for si =1:numSubCVD
    % load the 
    SubID   = Subs2checkCVD{si};
    load([ssvepPath SubID '.mat'])
    dataArrayCVD(:,:,si) = NormMatrix;
end

% Summary stats per group.
meanSSVEPHC    = mean(dataArrayHC,3);
stdSSVEPHC     = std(dataArrayHC,0,3);

meanSSVEPCVD    = mean(dataArrayCVD,3);
stdSSVEPCVD     = std(dataArrayCVD,0,3);

%% Permutation testing based on cluster size. 
nPerm   = 1000;
nHC     = 12; %subsample from the HC group
nCVD    = 9;  %subsample from the CVD group
pval    =  .05; % p-value threshold
sigThresh = norminv(1-pval/2); % note: two-tailed for the first run on permutation

% find randomized idxs for testing
condlabels = (1:(nHC + nCVD))>nHC; % 0 = HC, 1 = CVD

% initialize an array for permutated mean maps
permutedDiffs = zeros(10,10,nPerm);

for permi = 1:nPerm
    
    % I am randomly subsampling the group arrays.
    idxHC   = randperm(numSubHC,nHC);
    idxCVD  = randperm(numSubCVD,nCVD);
    
    dataHC   = dataArrayHC(:,:,idxHC);   % Subsample for HCs
    dataCVD   = dataArrayCVD(:,:,idxCVD); % Subsample for CVDs

    % put data together into one matrix
    dataPooled = cat(3,dataHC,dataCVD);
    
    % generate true condition labels
    numSubSamples    = size(dataPooled,3);

    % shuffle condition label vector
    fakeconds = condlabels( randperm(numSubSamples) );
    
    % compute and store difference time series
    mean1 = mean( dataPooled(:,:,fakeconds==0),3 ); % permutated HCs
    mean2 = mean( dataPooled(:,:,fakeconds==1),3 ); % permutated CVDs

    permutedDiffs(:,:,permi) = mean1-mean2;
end

%% find cluster sizes under the null hypothesis

% initialize cluster sizes and weights from permutation
clustsizes      = zeros(nPerm,1);
clusterWeights  = zeros(nPerm,1);

for permi=1:nPerm
    
    % compute z-score difference, permuted sets. Each permutation to the
    % distribution of permutations
    zdiffFake = (permutedDiffs(:,:,permi)-mean(permutedDiffs,3)) ./ std(permutedDiffs,[],3);
    
    % threshold using the significant threshold
    zdiffFake( abs(zdiffFake)<sigThresh ) = 0;
    
    % identify clusters. Points different than 0. 
    islands = bwconncomp( logical(zdiffFake) );
    
    % find cluster sizes
    clustNs = cellfun(@length,islands.PixelIdxList);

    % find max cluster size for the current permutation
    if ~isempty(clustNs)
        clustsizes(permi) = max(clustNs);
    else
        clustsizes(permi) = 0;
    end

    % find max cluster weight for the current permutation
    islandsclust  = islands.PixelIdxList;
    if ~isempty(islandsclust)
        % Create new cell array to store results
        newArr = cell(size(islandsclust));
        % Loop through islands
        for i = 1:numel(islandsclust)
            idx = islandsclust{i};
            if ~isempty(idx)
                newArr{i} = sum(abs(zdiffFake(idx))); % extract using linear indexing
            else
                newArr{i} = []; % store empty if no indices
            end
        end
    
        clusterWeights(permi) = max(cell2mat(newArr));
    end
end

% compute cluster threshold
clustSizethresh = prctile(clustsizes,100-pval*100);
clustDensthresh = prctile(clusterWeights,100-pval*100);

figure, clf; tiledlayout(1,2,"TileSpacing","tight","Padding","compact"); nexttile; hold on;
histogram(clustsizes)
xline(clustSizethresh,'r-.')
xlabel('Cluster size'), ylabel('Count')


nexttile; hold on;
histogram(clusterWeights)
xline(clustDensthresh,'r-.')
xlabel('Abs Cluster weight'), ylabel('Count')

figure;
hold on;
histogram(clusterWeights)
xline(clustDensthresh,'r-.')
xlabel('Abs. Cluster weight'), ylabel('Count')
%% remove small clusters from real thresholded data
% compute z-score difference. Observed (Real) to permuted data.
obsdiff = mean(dataArrayHC,3) - mean(dataArrayCVD,3);
zdiff   = (obsdiff-mean(permutedDiffs,3)) ./ std(permutedDiffs,[],3);

% recompute thresholded time series
zthresh = zdiff;
zthresh( abs(zthresh)<sigThresh ) = 0; % negative and positive clusters!!!!

% plot that
figure, clf; tiledlayout(2,3,"TileSpacing","compact","Padding","compact")
nexttile, hold on
imagesc(redArray,greenArray,zdiff); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000])
title('Differences between conditions HC - CVD')


nexttile, hold on
imagesc(redArray,greenArray,zthresh); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000])
title('Statistical results, uncorrected')

% find islands for the real data (same we did above for each distribution)
islands = bwconncomp( logical(zthresh) );
zthrDensity = zthresh;
% find and remove any subthreshold islands
for ii=1:islands.NumObjects
    if numel(islands.PixelIdxList{ii})<=clustSizethresh;
        zthresh(islands.PixelIdxList{ii}) = 0;
    end
end

% now plot that
nexttile, hold on
clusterCorrectedMap = zthresh;
imagesc(redArray,greenArray,clusterCorrectedMap); set(gca,'YDir','normal'); axis square;
clim([-1 1])
xlim([0 3200]); ylim([0 2000])
title('Statistical results, corrected by cluster size')


% find max cluster weight for the current permutation
islandsclust  = islands.PixelIdxList;
if ~isempty(islandsclust)
    % Create new cell array to store results
    newArr = cell(size(islandsclust));
    % Loop through islands
    for i = 1:numel(islandsclust)
        idx = islandsclust{i};
        if ~isempty(idx)
            newArr{i} = sum(abs(zthrDensity(idx))); % extract using linear indexing
        else
            newArr{i} = []; % store empty if no indices
        end
    end
end

for ii=1:islands.NumObjects
    if newArr{ii} <= clustDensthresh;
        zthrDensity(islands.PixelIdxList{ii}) = 0;
    end
end

nexttile; nexttile; 
nexttile; hold on
clusterCorrectedMap = zthrDensity;
imagesc(redArray,greenArray,clusterCorrectedMap); set(gca,'YDir','normal'); axis square;
clim([-3 3])
xlim([0 3200]); ylim([0 2000])
title('Statistical results, corrected by absolute cluster weight')

% find the aggregate z-scores and the p-values
clusters = bwconncomp( logical(zthrDensity) );
zscores  = zeros(2,1); pval = zeros(2,1);

for iii = 1:clusters.NumObjects
    values =  zthrDensity(clusters.PixelIdxList{iii});
    zscores(iii)    = sum(values);
    pval(iii)       = numel(find((clusterWeights > abs(sum(values)))))./(numel(clusterWeights));
end
%%
obsdiff = mean(dataArrayHC,3) - mean(dataArrayCVD,3);
zdiff   = (obsdiff-mean(permutedDiffs,3)) ./ std(permutedDiffs,[],3);

% recompute thresholded time series
zthresh = zdiff;
zthresh( abs(zthresh)<sigThresh ) = 0; % negative and positive clusters!!!!

% plot that
figure, clf; tiledlayout(1,3,"TileSpacing","compact","Padding","compact")
nexttile, hold on
imagesc(redArray,greenArray,zdiff); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
xlabel('Red (D/A)'); ylabel('Green (D/A)')
% title('Differences between conditions HC - CVD')

nexttile, hold on
imagesc(redArray,greenArray,zthresh); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
xlabel('Red (D/A)'); ylabel('Green (D/A)')
title('Statistical results, uncorrected')

nexttile; hold on
imagesc(redArray,greenArray,clusterCorrectedMap); set(gca,'YDir','normal'); axis square;
clim([-4 4])
xlim([0 3200]); ylim([0 2000])
title('Statistical results, corrected by absolute cluster weight')
xlabel('Red (D/A)'); ylabel('Green (D/A)')


%%
figure, clf; hold on
imagesc(redArray,greenArray,zdiff); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
xlabel('Red (D/A)'); ylabel('Green (D/A)')
% title('z-score differences between conditions HC - CVD')
cbar

figure, hold on
imagesc(redArray,greenArray,zthresh); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
xlabel('Red (D/A)'); ylabel('Green (D/A)')
title('Statistical results, uncorrected')
cbar

figure; hold on
imagesc(redArray,greenArray,clusterCorrectedMap); set(gca,'YDir','normal'); axis square;
clim([-4 4])
xlim([0 3200]); ylim([0 2000])
% title('Statistical results, corrected by absolute cluster weight')
xlabel('Red (D/A)'); ylabel('Green (D/A)')
cbar