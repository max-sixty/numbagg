import numpy as np
from numba import float32, float64

from .decorators import ndmoveexp, ndmoveexpmat


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64, float64[:]),
    ],
)
def move_exp_nancount(a, alpha, min_weight, out):
    N = len(a)

    count = weight = 0.0

    for i in range(N):
        a_i = a[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        count *= decay
        weight *= decay

        if not np.isnan(a_i):
            count += 1
            weight += alpha_i

        if weight >= min_weight:
            out[i] = count
        else:
            out[i] = np.nan


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64, float64[:]),
    ]
)
def move_exp_nanmean(a, alpha, min_weight, out):
    """
    Exponentially weighted moving mean
    """
    N = len(a)

    numer = denom = weight = 0.0

    for i in range(N):
        a_i = a[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        numer *= decay
        denom *= decay
        weight *= decay

        if not np.isnan(a_i):
            numer += a_i
            denom += 1.0
            weight += alpha_i

        if weight >= min_weight:
            out[i] = numer / denom
        else:
            out[i] = np.nan


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64, float64[:]),
    ]
)
def move_exp_nansum(a, alpha, min_weight, out):
    N = len(a)

    numer = weight = 0.0
    zero_count = True

    for i in range(N):
        a_i = a[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        numer *= decay
        weight *= decay

        if not np.isnan(a_i):
            zero_count = False
            numer += a_i
            weight += alpha_i

        if weight >= min_weight and not zero_count:
            out[i] = numer
        else:
            out[i] = np.nan


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64, float64[:]),
    ]
)
def move_exp_nanvar(a, alpha, min_weight, out):
    N = len(a)

    # sum_x: decayed sum of the sequence values.
    # sum_x2: decayed sum of the squared sequence values.
    # n: decayed count of non-missing values observed so far in the sequence.
    # n2: decayed sum of the (already-decayed) weights of non-missing values.
    sum_x_2 = sum_x = sum_weight = sum_weight_2 = weight = 0.0

    for i in range(N):
        a_i = a[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        # decay the values
        sum_x_2 *= decay
        sum_x *= decay
        sum_weight *= decay
        # We decay this twice because we want the weight^2, so need to decay again
        # (We could explain this better; contributions welcome...)
        sum_weight_2 *= decay**2
        weight *= decay

        if not np.isnan(a_i):
            sum_x_2 += a_i**2
            sum_x += a_i
            sum_weight += 1.0
            sum_weight_2 += 1.0
            weight += alpha_i

        var_biased = (sum_x_2 / sum_weight) - ((sum_x / sum_weight) ** 2)

        # - Ultimately we want `sum(weights_norm**2)`, where `weights_norm` is
        #   `weights / sum(weights)`:
        #
        #   sum(weights_norm**2)
        #   = sum(weights**2 / sum(weights)**2)
        #   = sum(weights**2) / sum(weights)**2
        #   = sum_weight_2 / sum_weight**2
        bias = 1 - sum_weight_2 / (sum_weight**2)

        if weight >= min_weight and bias > 0:
            out[i] = var_biased / bias
        else:
            out[i] = np.nan


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64, float64[:]),
    ]
)
def move_exp_nanstd(a, alpha, min_weight, out):
    """
    Calculates the exponentially decayed standard deviation.

    Note that technically the unbiased weighted standard deviation is not exactly the
    same as the square root of the unbiased weighted variance, since the bias is
    concave. But it's close, and it's what pandas does.

    (If anyone knows the math well and wants to take a pass at improving it,
    contributions are welcome.)
    """
    # This is very similar to `move_exp_nanvar`, but square-roots in the final step. It
    # could be implemented as a wrapper around `move_exp_nanvar`, but it causes a couple
    # of small complications around warnings for `np.sqrt` on invalid values, and passing
    # the `axis` parameter, such that it was easier to just copy-pasta.

    N = len(a)

    # sum_x: decayed sum of the sequence values.
    # sum_x2: decayed sum of the squared sequence values.
    # n: decayed count of non-missing values observed so far in the sequence.
    # n2: decayed sum of the (already-decayed) weights of non-missing values.
    sum_x_2 = sum_x = sum_weight = sum_weight_2 = weight = 0.0

    for i in range(N):
        a_i = a[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        # decay the values
        sum_x_2 *= decay
        sum_x *= decay
        sum_weight *= decay
        # We decay this twice because we want the weight^2, so need to decay again
        # (We could explain this better; contributions welcome...)
        sum_weight_2 *= decay**2
        weight *= decay

        if not np.isnan(a_i):
            sum_x_2 += a_i**2
            sum_x += a_i
            sum_weight += 1.0
            sum_weight_2 += 1.0
            weight += alpha_i

        var_biased = (sum_x_2 / sum_weight) - ((sum_x / sum_weight) ** 2)

        # - Ultimately we want `sum(weights_norm**2)`, where `weights_norm` is
        #   `weights / sum(weights)`:
        #
        #   sum(weights_norm**2)
        #   = sum(weights**2 / sum(weights)**2)
        #   = sum(weights**2) / sum(weights)**2
        #   = sum_weight_2 / sum_weight**2
        bias = 1 - sum_weight_2 / (sum_weight**2)

        if weight >= min_weight and bias > 0:
            out[i] = np.sqrt(var_biased / bias)
        else:
            out[i] = np.nan


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64[:], float64, float64[:]),
    ]
)
def move_exp_nancov(a1, a2, alpha, min_weight, out):
    N = len(a1)

    # sum_x1: decayed sum of the sequence values for a1.
    # sum_x2: decayed sum of the sequence values for a2.
    # sum_x1x2: decayed sum of the product of sequence values for a1 and a2.
    # sum_weight: decayed count of non-missing values observed so far in the sequence.
    # sum_weight_2: decayed sum of the (already-decayed) weights of non-missing values.
    sum_x1 = sum_x2 = sum_x1x2 = sum_weight = sum_weight_2 = weight = 0.0

    for i in range(N):
        a1_i = a1[i]
        a2_i = a2[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        # decay the values
        sum_x1 *= decay
        sum_x2 *= decay
        sum_x1x2 *= decay
        sum_weight *= decay
        sum_weight_2 *= decay**2
        weight *= decay

        if not (np.isnan(a1_i) or np.isnan(a2_i)):
            sum_x1 += a1_i
            sum_x2 += a2_i
            sum_x1x2 += a1_i * a2_i
            sum_weight += 1
            sum_weight_2 += 1
            weight += alpha_i

        cov_biased = ((sum_x1x2) - (sum_x1 * sum_x2 / sum_weight)) / sum_weight

        # Adjust for the bias. (explained in `move_exp_nanvar`)
        bias = 1 - sum_weight_2 / (sum_weight**2)

        if weight >= min_weight and bias > 0:
            out[i] = cov_biased / bias
        else:
            out[i] = np.nan


@ndmoveexpmat.wrap(
    signature=[
        (float32[:, :], float32[:], float32, float32[:, :, :]),
        (float64[:, :], float64[:], float64, float64[:, :, :]),
    ],
    gufunc_signature="(k,n),(n),()->(n,k,k)",
)
def move_exp_nancorrmat(arr, alpha, min_weight, out):
    """
    Calculates the exponentially decayed correlation matrix between columns of input array.

    Parameters
    ----------
    arr : array
        Input array of shape (n,k) where n is time and k is number of variables
    alpha : array
        Alpha values for exponential weighting
    min_weight : float
        Minimum weight required to compute correlation
    out : array
        Output array for correlation matrix values (n,k,k)
    """
    N = arr.shape[1]  # number of time points (axis 1)
    K = arr.shape[0]  # number of variables (axis 0)
    # Arrays to store sums and squared sums for each column
    sums = np.zeros(K)
    sum_sqs = np.zeros(K)
    # Array to store cross products between columns
    sum_prods = np.zeros((K, K))

    # Track weights per pair
    weights = np.zeros((K, K))
    sum_weights = np.zeros((K, K))
    sum_weights_2 = np.zeros((K, K))

    for i in range(N):
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        # Decay all values
        sums *= decay
        sum_sqs *= decay
        sum_prods *= decay
        weights *= decay
        sum_weights *= decay
        sum_weights_2 *= decay**2

        # Update sums and cross products for valid pairs
        for k in range(K):
            val_k = arr[k, i]
            if not np.isnan(val_k):
                sums[k] += val_k
                sum_sqs[k] += val_k * val_k

                for j in range(k + 1, K):
                    val_j = arr[j, i]
                    if not np.isnan(val_j):
                        prod = val_k * val_j
                        sum_prods[k, j] += prod
                        sum_prods[j, k] += prod
                        # Update weights only for valid pairs
                        weights[k, j] += alpha_i
                        weights[j, k] += alpha_i
                        sum_weights[k, j] += 1
                        sum_weights[j, k] += 1
                        sum_weights_2[k, j] += 1
                        sum_weights_2[j, k] += 1

        # Compute correlations for each pair
        for k in range(K):
            for j in range(k, K):  # Include diagonal
                # The bias cancels out in correlation, but we keep the check for consistency
                bias = 1 - sum_weights_2[k, j] / (sum_weights[k, j]**2)

                if weights[k, j] >= min_weight and bias > 0:
                    # For diagonal elements, correlation is always 1.0
                    if k == j:
                        out[i, k, k] = 1.0
                    else:
                        # Compute variances and covariance
                        var_k = sum_sqs[k] - (sums[k] ** 2 / sum_weights[k, j])
                        var_j = sum_sqs[j] - (sums[j] ** 2 / sum_weights[k, j])
                        cov = sum_prods[k, j] - (sums[k] * sums[j] / sum_weights[k, j])

                        # Compute correlation if possible
                        denominator = np.sqrt(var_k * var_j)
                        if denominator > 0:
                            corr = cov / denominator
                            out[i, k, j] = out[i, j, k] = corr
                        else:
                            out[i, k, j] = out[i, j, k] = np.nan
                else:
                    out[i, k, j] = out[i, j, k] = np.nan


@ndmoveexp.wrap(
    [
        (float32[:], float32[:], float32[:], float32, float32[:]),
        (float64[:], float64[:], float64[:], float64, float64[:]),
    ]
)
def move_exp_nancorr(a1, a2, alpha, min_weight, out):
    N = len(a1)

    sum_x1 = sum_x2 = sum_x1x2 = sum_weight = sum_weight_2 = 0
    weight = sum_x1_2 = sum_x2_2 = 0

    for i in range(N):
        a1_i = a1[i]
        a2_i = a2[i]
        alpha_i = alpha[i]
        decay = 1.0 - alpha_i

        sum_x1 *= decay
        sum_x2 *= decay
        sum_x1x2 *= decay
        sum_weight *= decay
        sum_weight_2 *= decay**2
        weight *= decay

        sum_x1_2 *= decay
        sum_x2_2 *= decay

        if not (np.isnan(a1_i) or np.isnan(a2_i)):
            sum_x1 += a1_i
            sum_x2 += a2_i
            sum_x1x2 += a1_i * a2_i
            sum_weight += 1
            sum_weight_2 += 1
            weight += alpha_i
            sum_x1_2 += a1_i**2
            sum_x2_2 += a2_i**2

        # The bias cancels out, so we don't need to adjust for it

        cov = sum_x1x2 - (sum_x1 * sum_x2 / sum_weight)
        var_a1 = sum_x1_2 - (sum_x1**2 / sum_weight)
        var_a2 = sum_x2_2 - (sum_x2**2 / sum_weight)

        # TODO: we don't need to compute this for the output, but if we don't, then we
        # get an error around numerical precision that causes us to produce values when
        # we shouldn't. Would be good to be able to remove it. (This is well-tested, so
        # if we can remove it while passing tests, then we can.)
        bias = 1 - sum_weight_2 / (sum_weight**2)

        if weight >= min_weight and bias > 0:
            denominator = np.sqrt(var_a1 * var_a2)
            if denominator > 0:
                out[i] = cov / denominator
            else:
                out[i] = np.nan
        else:
            out[i] = np.nan
