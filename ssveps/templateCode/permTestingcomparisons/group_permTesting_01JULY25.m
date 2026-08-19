clear all;

ssvepPath   = 'C:\Users\zevaz\OneDrive\Escritorio\Metamers\eegExp\SSVEPGRIDdataResults\';

Subs2checkHC = {'MET000' 'MET000b' 'MET001' 'MET002' 'MET002b' 'MET003' 'MET003b' 'MET004' 'MET004b' 'MET005b' 'MET005c' 'MET006' 'MET006b' 'MET007' 'MET008' 'MET008b' 'MET009' 'MET009b' 'MET010'...
              'MET011' 'MET012' 'MET018' 'MET018b' 'MET020' 'MET021' 'MET021b' 'MET022' 'MET023' 'MET023b' 'MET024' 'MET026' 'MET027' 'MET027b'};

Subs2checkCVD = {'MET015' 'MET016' 'MET016b' 'MET017' 'MET017b' 'MET028' 'MET029'};

%% 
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

for si =1:numSubCVD
    % load the 
    SubID   = Subs2checkCVD{si};
    load([ssvepPath SubID '.mat'])
    dataArrayCVD(:,:,si) = NormMatrix;
end

meanSSVEPHC    = mean(dataArrayHC,3);
stdSSVEPHC     = std(dataArrayHC,0,3);

meanSSVEPCVD    = mean(dataArrayCVD,3);
stdSSVEPCVD     = std(dataArrayCVD,0,3);


%% 
nPerm   = 1000;
nHC     = 30;
nCVD    = 5;
pval    =  .05; % p-value threshold
sigThresh = norminv(1-pval/2); % note: two-tailed for the first run on permutation

% find randomized idxs for testing
condlabels = (1:(nHC + nCVD))>nHC; % 0 = HC, 1 = CVD

% initialize
permutedDiffs = zeros(10,10,nPerm);

for permi = 1:nPerm
    
    % I am subsampling the real arrays. Not sure why, but it felt right.
    idxHC   = randperm(numSubHC,nHC);
    idxCVD  = randperm(numSubCVD,nCVD);
    
    data1   = dataArrayHC(:,:,idxHC);   % Subsample for HCs
    data2   = dataArrayCVD(:,:,idxCVD); % Subsample for CVDs

    % put data together into one matrix
    dataPooled = cat(3,data1,data2);
    
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

% initialize cluster sizes from permutation
clustsizes = zeros(nPerm,1);

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
end

% compute cluster threshold
clustthresh = prctile(clustsizes,100-pval*100);

figure, clf
histogram(clustsizes)
xline(clustthresh,'r-.')
xlabel('Cluster size'), ylabel('Count')

%% remove small clusters from real thresholded data

% compute z-score difference. Observed (Real) to permuted data
obsdiff = mean(dataArrayHC,3) - mean(dataArrayCVD,3);
zdiff   = (obsdiff-mean(permutedDiffs,3)) ./ std(permutedDiffs,[],3);

% recompute thresholded time series
zthresh = zdiff;
zthresh( abs(zthresh)<sigThresh ) = 0; % negative and positive clusters!!!!

% plot that
figure, clf; tiledlayout(1,3,"TileSpacing","compact","Padding","compact")
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

% find and remove any subthreshold islands
for ii=1:islands.NumObjects
    if numel(islands.PixelIdxList{ii})<=clustthresh
        zthresh(islands.PixelIdxList{ii}) = 0;
    end
end

% now plot that
nexttile, hold on
clusterCorrectedMap = zthresh;
imagesc(redArray,greenArray,clusterCorrectedMap); set(gca,'YDir','normal'); axis square;
clim([-1 1])
xlim([0 3200]); ylim([0 2000])
title('Statistical results, corrected')































% %% plot them all in the same figure;
% Subs2check = {'MET000' 'MET000b' 'MET001' 'MET002' 'MET002b' 'MET003' 'MET003b' 'MET004' 'MET004b' 'MET005b' 'MET005c' 'MET006' 'MET006b' 'MET007' 'MET008' 'MET009' 'MET009b' 'MET010'...
%               'MET011' 'MET012' 'MET018' 'MET018b' 'MET020' 'MET021' 'MET021b' 'MET022' 'MET023' 'MET023b' 'MET024' 'MET026' 'MET027' 'MET027b'...
%               'MET015' 'MET016' 'MET016b' 'MET017' 'MET017b' 'MET028' 'MET029'};
% groupLabels = [repmat("healthy", 32, 1); repmat("CVDd",1 , 1); repmat("CVDp",5 , 1); repmat("CVDd",1 , 1)];
% 
% numSub     = numel(Subs2check); 
% dataArray  = zeros(10, 10, numSub);
% 
% % array for Healthy controls
% for si =1:numSub
%     % load the 
%     SubID   = Subs2check{si};
%     load([ssvepPath SubID '.mat'])
%     dataArray(:,:,si) = NormMatrix;
% end
% 
% pathsave = 'C:\Users\zevaz\OneDrive\Escritorio\Metamers\eegExp\';
% pathFileName = 'shareData.mat';
% 
% save([pathsave pathFileName],"dataArray","groupLabels","redArray","greenArray");