function [zmap,zmapthre,max_cluster_size,zweight,numPix] = getzscoremap(set2check,meanMap,stdMap,pval)
%GETZSCOREMAP Computes z-score map and extracts significant clusters.
%
%   [zmap, zmapthre, max_cluster_size, zweight, numPix] = GETZSCOREMAP(set2check, meanMap, stdMap, pval)
%
%   This function computes a z-score map from an input dataset and applies
%   a statistical threshold to identify significant clusters using a
%   two-tailed test. It returns the raw z-map, a thresholded z-map, the size
%   of the largest significant cluster, the summed z-score within that
%   cluster (zweight), and the total number of significant pixels.
%
%   INPUTS:
%     set2check  - Data to be z-scored (e.g., a single subject or test map)
%     meanMap    - Mean map (e.g., from permutations or null distribution)
%     stdMap     - Standard deviation map corresponding to meanMap
%     pval       - Significance level for thresholding (two-tailed)
%
%   OUTPUTS:
%     zmap            - The full z-score map: (set2check - meanMap) ./ stdMap
%     zmapthre        - Thresholded z-map, with non-significant values set to 0
%     max_cluster_size- Size (in pixels) of the largest contiguous suprathreshold cluster
%     zweight         - Sum of z-values within the largest cluster (cluster "weight")
%     numPix          - Total number of suprathreshold pixels across the map
%
%   NOTES:
%     - The function uses a two-tailed normal inverse (norminv) to compute the
%       threshold based on the specified p-value.
%     - Clustering is performed using 2D connectivity (default behavior of bwconncomp).
%
%   Example:
%     [zmap, zmapthre, max_size, weight, numpix] = getzscoremap(data, nullMean, nullStd, 0.05);
%
    sigThresh = norminv(1-pval/2); % note: two-tailed for the first run on permutation
    zmap = (set2check - meanMap)./stdMap;
    zmapthre = zmap;
    zmapthre( abs(zmapthre)<sigThresh ) = 0;
    
    islands = bwconncomp(zmapthre);
    if numel(islands.PixelIdxList)>0
        
        % count sizes of clusters
        tempclustsizes = cellfun(@length,islands.PixelIdxList);
        
        % store size of biggest cluster
        [max_cluster_size idx]= max(tempclustsizes);
        zweight = sum(zmapthre(islands.PixelIdxList{idx})); 
    else
        max_cluster_size = 0; zweight = 0;
    end
    
    numPix  = numel(find(zmapthre)); 
end