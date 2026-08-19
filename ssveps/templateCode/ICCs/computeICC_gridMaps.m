function [r, LB, UB, F, df1, df2, p] = computeICC_gridMaps(pairsIDx, pairsIDs,cellResult)
%UNTITLED4 Summary of this function goes here
%   Detailed explanation goes here
flatList = string([pairsIDs{:}]);
disp(flatList);

indexPairs = cell2mat(pairsIDx'); % now, these are the indices for session 1 and 2 respectively. 
numpairs   = size(indexPairs,1);

% loop each HC group.
numPix = 100;
arraySe1        = zeros(10, 10,numpairs);
arrayFlatS1     = zeros(numpairs,numPix);
arraySe2        = zeros(10, 10,numpairs);
arrayFlatS2     = zeros(numpairs,numPix);

for hi = 1:numpairs
    idxSe1        = indexPairs(hi,1);
    idxSe2        = indexPairs(hi,2);

    % get the data for session 1. 
    dataSe1          = cellResult{idxSe1};
    numberTrials    = size(dataSe1.runMap,3);
    subBase         = dataSe1.baselines;
    subGrid         = dataSe1.runMap;
    NormRuns        = zeros(10,10,numberTrials);
    for runi = 1:numberTrials
        baseRuni = mean(squeeze(subBase(:,runi)));
        gridRuni = squeeze(subGrid(:,:,runi));
        NormRuns(:,:,runi) = (gridRuni - baseRuni)./baseRuni; 
    end
    NormMatrix = mean(NormRuns,3);
    arraySe1(:,:,hi) = NormMatrix;
    reshaped = reshape(NormMatrix, 1, []);  % convert 10x10 to 1x100
    arrayFlatS1(hi,:) = reshaped';

    % get the data for session 2. 
    dataSe2          = cellResult{idxSe2};
    numberTrials    = size(dataSe2.runMap,3);
    subBase         = dataSe2.baselines;
    subGrid         = dataSe2.runMap;
    NormRuns        = zeros(10,10,numberTrials);
    for runi = 1:numberTrials
        baseRuni = mean(squeeze(subBase(:,runi)));
        gridRuni = squeeze(subGrid(:,:,runi));
        NormRuns(:,:,runi) = (gridRuni - baseRuni)./baseRuni; 
    end
    NormMatrix = mean(NormRuns,3);
    arraySe2(:,:,hi) = NormMatrix;
    reshaped = reshape(NormMatrix, 1, []);  % convert 10x10 to 1x100
    arrayFlatS2(hi,:) = reshaped';
end

%% for each pixel in the map 

for pi = 1:numPix
    pixs1 = arrayFlatS1(:,pi);
    pixs2 = arrayFlatS2(:,pi);

    %% do ICC
    [r(pi), LB(pi), UB(pi), F(pi), df1(pi), df2(pi), p(pi)] = ICC([pixs1 pixs2], 'A-1') ; % measures agreement between the 2 measurements. 
end

end