clear all; 
loadFolder = 'C:\Users\zevaz\OneDrive\Escritorio\Metamers\eegExp\results\rawGRIDFBCCA\';
cd(loadFolder)

load('groupData.mat'); % loads cellResults
numSubinDataset = numel(cellResult);

[redArray,greenArray,allIdx,allIDs] = findAllElementsWithRepeatedSessions();
[onlyCTRIDx,onlyCTRIDs] = filterOnlyHealthy(allIdx);

%% show the names of the only CTR people.
for subi = 1:numel(onlyCTRIDs)
    onlyCTRIDs{subi}
end

%% show the names of the whole geoup that we have 2 runs for. 
for subi = 1:numel(allIDs)
    allIDs{subi}
end

%% Get the ICC info for the whole group. 
[ICCall, LBall, UBall, Fall, df1all, df2all, pall] = computeICC_gridMaps(allIdx, allIDs,cellResult);
%% Get the ICC info for the group with only CTR. 
[ICCctr, LBctr, UBctr, Fctr, df1ctr, df2ctr, pctr] = computeICC_gridMaps(onlyCTRIDx, onlyCTRIDs,cellResult);

%% now plot these and get info to output. For all
ICCall_reshaped = reshape(ICCall, 10, 10);
meanICCall = mean(ICCall_reshaped,'all');
mediananICCall = median(ICCall_reshaped,'all');

figure;
colormap("parula")
imagesc(redArray,greenArray, ICCall_reshaped); set(gca,'YDir','normal'); hold on; %title(['ICC3 agreement ALL, mean ' num2str(meanICCall,2) ', med = ' num2str(mediananICCall,2)], 'FontSize', 16); hold on;
axis square; clim([0 1]);set(gca,'YDir','normal'); hold on; 
set(gca, 'FontSize', 16, 'XColor', 'w', 'YColor', 'w');   % Axes tick labels
xlabel('Red LED (D/A units)', 'FontSize', 16, 'Color', 'w');
ylabel('Green LED (D/A units)', 'FontSize', 16, 'Color', 'w');

a = colorbar;
a.Label.String = 'ICC';
a.Label.Color = 'w';     % Colorbar label
a.Color = 'w';           % Colorbar tick labels
xticks(floor(redArray)); xtickangle(0)
yticks(floor(greenArray))
xlabel('Red LED (D/A units)', 'FontSize', 14); ylabel('Green LED (D/A units)', 'FontSize', 14);
a=colorbar;
a.Label.String = 'ICC';

%% now plot CTR only
ICCctr_reshaped= reshape(ICCctr, 10, 10);
meanICCctr     = mean(ICCctr_reshaped,'all');
medianICCctr   = median(ICCctr_reshaped,'all');

figure;
imagesc(redArray,greenArray, ICCctr_reshaped); set(gca,'YDir','normal'); hold on; title(['ICC3 agreement CTR, mean ' num2str(meanICCctr,2) ', med = ' num2str(medianICCctr,2)], 'FontSize', 16); hold on;
axis square; clim([0 1]);set(gca,'YDir','normal'); hold on; 
xticks(floor(redArray)); xtickangle(0)
yticks(floor(greenArray))
xlabel('Red LED (D/A units)', 'FontSize', 14); ylabel('Green LED (D/A units)', 'FontSize', 14)
a=colorbar;
a.Label.String = 'ICC';

%%
points2use = [0 1111; 2488 222; 3200 1333; 711 1777; 2133 2000];

[idxGreen, idxRed] = getIndicesForSelectedPixels(redArray,greenArray, points2use);

ICC5pixctr = zeros(1,numel(idxGreen));
ICC5pixAll = zeros(1,numel(idxGreen));

for xi = 1:numel(idxGreen) 
    ICC5pixAll(xi)      = ICCall_reshaped(idxRed(xi),idxGreen(xi)); 
    ICC5pixctr(xi)      = ICCctr_reshaped(idxRed(xi),idxGreen(xi)); 
end

[mean(ICC5pixctr) median(ICC5pixctr)]
[mean(ICC5pixAll) median(ICC5pixAll)]

%%

[~, ~, allSSVEP1, allSSVEP2] = getpairsOfSSVEPs(allIdx, allIDs, cellResult); 
[~, ~, ctrSSVEP1, ctrSSVEP2] = getpairsOfSSVEPs(onlyCTRIDx, onlyCTRIDs, cellResult);

% grab the values we care about. 
numSubAll = size(allSSVEP1,3);
session1all = zeros(numel(idxGreen), numSubAll);
session2all = zeros(numel(idxGreen), numSubAll);

for si = 1:numSubAll
    for idi =1:numel(idxGreen)
        session1all(idi,si) = allSSVEP1(idxRed(idi),idxGreen(idi),si);
        session2all(idi,si) = allSSVEP2(idxRed(idi),idxGreen(idi),si);
    end
end

numSubctr = size(ctrSSVEP1,3);
session1ctr = zeros(numel(idxGreen), numSubctr);
session2ctr = zeros(numel(idxGreen), numSubctr);

for si = 1:numSubctr
    for idi =1:numel(idxGreen)
        session1ctr(idi,si) = ctrSSVEP1(idxRed(idi),idxGreen(idi),si);
        session2ctr(idi,si) = ctrSSVEP2(idxRed(idi),idxGreen(idi),si);
    end
end

%% blandAlmant
figure
t = tiledlayout(2,3,"TileSpacing","tight","Padding","compact");
for pli = 1:5
    nexttile;
    plotBlandAltman(session1all(pli,:), session2all(pli,:))
    axis square
end


figure
t = tiledlayout(1,5,"TileSpacing","tight","Padding","compact");
for pli = 1:5
    nexttile;
    plotBlandAltman(session1ctr(pli,:), session2ctr(pli,:))
end

%% scatter plots
figure
t = tiledlayout(1,5,"TileSpacing","tight","Padding","compact");
for pli = 1:5
    nexttile;
    plotSessionScatterByParticipant(session1all(pli,:), session2all(pli,:))
end

figure
t = tiledlayout(1,5,"TileSpacing","tight","Padding","compact");
for pli = 1:5
    nexttile;
    plotSessionScatterByParticipant(session1ctr(pli,:), session2ctr(pli,:))
end

