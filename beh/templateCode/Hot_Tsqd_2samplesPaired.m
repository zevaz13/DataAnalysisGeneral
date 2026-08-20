function [pvalue,h,T_sqd] = Hot_Tsqd_2samplesPaired(x,y,alpha)
%Hot_Tsqd_2samp Hotelling Tsqd 2 samples 
% x (numSamp, dimensions)
% y (numSamp, dimensions)
% alpha <- statistical value to compare against
    % find difference
    diffe = x - y;
    % get the number of elements
    nd = length(diffe);
    % number of dimensions
    p = size(diffe,2);
    % get the man of differences
    diffMean = mean(diffe)';
    % get the covariance
    Sd = cov(diffe);
    % Hotelling Tsqd
    T_sqd = nd*diffMean'*inv(Sd)*diffMean;
    v = nd-1;
    F = (v-p+1) / (v*p) * T_sqd;
    pvalue = 1-fcdf(F,p,v-p+1);
    % then we need to compare to the alpha value
    
    if pvalue < alpha
        h = 1;
    else 
        h = 0; 
    end
end

