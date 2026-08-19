clear all;

%% This script performs permutation based testing using the SSVEP maps, between the groups. This script aims to find directional differences in the maps.
% instead of only asking whether there is a difference between them, it
% will use the z-scores to get cluster weights.

% where is the data
ssvepPath   = 'C:\Users\zevaz\OneDrive\Escritorio\Metamers\eegExp\SSVEPGRIDdataResults\';

% Sets from the healthy group
Subs2checkHC = {'MET000' 'MET000b' 'MET001' 'MET002' 'MET002b' 'MET003' 'MET003b' 'MET004' 'MET004b' 'MET005b' 'MET005c' 'MET006' 'MET006b' 'MET007' 'MET008' 'MET008b' 'MET009' 'MET009b' 'MET010'...
              'MET011' 'MET012' 'MET018' 'MET018b' 'MET020' 'MET021' 'MET021b' 'MET022' 'MET023' 'MET023b' 'MET024' 'MET026' 'MET027' 'MET027b'};

% Sets from the CVD group
Subs2checkCVD = {'MET015' 'MET016' 'MET016b' 'MET017' 'MET017b' 'MET028' 'MET029' 'MET032' 'MET033' 'MET034'};

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

%% Permutation testing based on cluster size. 
nPerm   = 1000;
nHC     = 20; %subsample from the HC group
nCVD    = 5;  %subsample from the CVD group
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
clustsizesPOS      = zeros(nPerm,1);
clusterWeightsPOS  = zeros(nPerm,1);
clustsizesNEG      = zeros(nPerm,1);
clusterWeightsNEG  = zeros(nPerm,1);

for permi=1:nPerm
    
    % compute z-score difference, permuted sets. Each permutation to the
    % distribution of permutations
    zdiffFake = (permutedDiffs(:,:,permi)-mean(permutedDiffs,3)) ./ std(permutedDiffs,[],3);    
    % threshold using the significant threshold
    zdiffFake( abs(zdiffFake)<sigThresh ) = 0;    
    % identify clusters. Points different than 0. 
    islands = bwconncomp( logical(zdiffFake) );    
    % find max cluster weight for the current permutation
    islandsclust  = islands.PixelIdxList;
    if ~isempty(islandsclust)
        % Create new cell array to store results
        newArr = cell(size(islandsclust));
        % Loop through islands
        for i = 1:numel(islandsclust)
            idx = islandsclust{i};
            if ~isempty(idx)
                newArr{i} = sum(zdiffFake(idx)); % extract using linear indexing
            else
                newArr{i} = []; % store empty if no indices
            end
        end
        
        if ~isempty(newArr)
            arrayWeight = cell2mat(newArr);
            arrayPOS =  arrayWeight > 0;
            arrayNEG =  arrayWeight < 0;
            
            posClusts = islandsclust(arrayPOS);
            if ~isempty(posClusts)
                posClN = cellfun(@length,posClusts);
                clustsizesPOS(permi) = max(posClN);

                newArrP = cell(size(posClusts));
                % Loop through islands
                for i = 1:numel(posClusts)
                    idx = posClusts{i};
                    if ~isempty(idx)
                        newArrP{i} = sum(zdiffFake(idx)); % extract using linear indexing
                    else
                        newArrP{i} = []; % store empty if no indices
                    end
                end
            clusterWeightsPOS(permi) = max(cell2mat(newArrP));
            end

            negClusts = islandsclust(arrayNEG);
            if ~isempty(negClusts)
                negClN = cellfun(@length,negClusts);
                clustsizesNEG(permi) = max(negClN);
                newArrP = cell(size(negClusts));
                % Loop through islands
                for i = 1:numel(negClusts)
                    idx = negClusts{i};
                    if ~isempty(idx)
                        newArrP{i} = sum(zdiffFake(idx)); % extract using linear indexing
                    else
                        newArrP{i} = []; % store empty if no indices
                    end
                end
            clusterWeightsNEG(permi) = max(cell2mat(newArrP));
            end
        end
    end
end

% compute cluster threshold
clustSizethreshPOS = prctile(clustsizesPOS,100-(pval/2)*100);
clustDensthreshPOS = prctile(clusterWeightsPOS,100-(pval/2)*100);
clustSizethreshNEG = prctile(clustsizesNEG,100-(pval/2)*100);
clustDensthreshNEG = prctile(clusterWeightsNEG,(pval/2)*100);

%% plot positive statistical attributes
figure, clf; tiledlayout(1,2,"TileSpacing","tight","Padding","compact"); nexttile; hold on;
histogram(clustsizesPOS)
xline(clustSizethreshPOS,'r-.')
xlabel('Positive Cluster size'), ylabel('Count')


nexttile; hold on;
histogram(clusterWeightsPOS)
xline(clustDensthreshPOS,'r-.')
xlabel('Positive Cluster weight'), ylabel('Count')

sgtitle('Distribution of positive clusters (sizes and weights)')

%% plot negative statistical attributes
figure, clf; tiledlayout(1,2,"TileSpacing","tight","Padding","compact"); nexttile; hold on;
histogram(clustsizesNEG)
xline(clustSizethreshNEG,'r-.')
xlabel('Negative Cluster size'), ylabel('Count')

nexttile; hold on;
histogram(clusterWeightsNEG)
xline(clustDensthreshNEG,'r-.')
xlabel('Negative Cluster weight'), ylabel('Count')

sgtitle('Distribution of Negative clusters (sizes and weights)')

%% remove small clusters from real thresholded data
% compute z-score difference. Observed (Real) to permuted data.
obsdiff = mean(dataArrayHC,3) - mean(dataArrayCVD,3);
zdiff   = (obsdiff-mean(permutedDiffs,3)) ./ std(permutedDiffs,[],3);

% recompute thresholded time series
zthresh = zdiff;
zthresh( abs(zthresh)<sigThresh ) = 0; % Thresholds both negative and positive pixels!!!!

% plot that

% find islands for the real data (same we did above for each distribution)
islands = bwconncomp( logical(zthresh) );

islandsclust  = islands.PixelIdxList;
if ~isempty(islandsclust)
    % Create new cell array to store results
    newArr = cell(size(islandsclust));
    % Loop through islands
    for i = 1:numel(islandsclust)
        idx = islandsclust{i};
        if ~isempty(idx)
            newArr{i} = sum(zthresh(idx)); % extract using linear indexing
        else
            newArr{i} = []; % store empty if no indices
        end
    end
end

% allocate arrays for resulting. These need to be masked by size. 
zthrSizePOS    = zthresh;
zthrDensityPOS = zthresh;

zthrSizeNEG    = zthresh;
zthrDensityNEG = zthresh;

if ~isempty(newArr)
    arrayWeight = cell2mat(newArr);
    arrayPOS =  arrayWeight > 0;
    arrayNEG =  arrayWeight < 0;
    
    posClusts = islandsclust(arrayPOS);
    negCluist = islandsclust(arrayNEG);
    
    % for positive clusters, only positive values should remain
    for ni = 1:numel(negCluist)
        zthrSizePOS(negCluist{ni}) = 0;
        zthrDensityPOS(negCluist{ni}) = 0;
    end

    % for negative clusters, only negative values remain
    for pi = 1:numel(posClusts)
        zthrSizeNEG(posClusts{pi}) = 0;
        zthrDensityNEG(posClusts{pi}) = 0;
    end


    %% find and mask the positive islands based on cluster sizes
    % positive cluster sizes
    for ii=1:numel(posClusts)
        if numel(posClusts{ii})<=clustSizethreshPOS
            zthrSizePOS(posClusts{ii}) = 0;
        end
    end
    % negative cluster sizes
    for ii=1:numel(negCluist)
        if numel(negCluist{ii})<=clustSizethreshNEG
            zthrSizeNEG(negCluist{ii}) = 0;
        end
     end

    % find and mask positive islandas based on cumulative Z-scores
    if ~isempty(posClusts)
        posWeights      = cell2mat(newArr(arrayPOS));
        for ii=1:numel(posWeights)
            if posWeights(ii)<=clustDensthreshPOS
                zthrDensityPOS(posClusts{ii}) = 0;
            end
        end
    end

    % find and mask positive islandas based on cumulative Z-scores
    if ~isempty(negCluist)
        negWeights      = cell2mat(newArr(arrayNEG));
        for ii=1:numel(negWeights)
            if negWeights(ii)>=clustDensthreshNEG
                zthrDensityNEG(negCluist{ii}) = 0;
            end
        end
    end
end

figure, clf; tiledlayout(3,2,"TileSpacing","compact","Padding","compact")
nexttile, hold on
imagesc(redArray,greenArray,zdiff); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000])
title('Differences between conditions HC - CVD')

nexttile, hold on
imagesc(redArray,greenArray,zthresh); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
title('Statistical results, uncorrected')

nexttile, hold on
imagesc(redArray,greenArray,zthrSizePOS); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); 
title('Statistical results, Corrected by positive cluster sizes')

nexttile, hold on
imagesc(redArray,greenArray,zthrDensityPOS); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
title('Statistical results, Corrected by positive cluster Weights')

nexttile, hold on
imagesc(redArray,greenArray,zthrSizeNEG); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
title('Statistical results, Corrected by negative cluster sizes')

nexttile, hold on
imagesc(redArray,greenArray,zthrDensityNEG); set(gca,'YDir','normal'); axis square;
xlim([0 3200]); ylim([0 2000]); clim([-4 4]);
title('Statistical results, Corrected by negative cluster Weights')
