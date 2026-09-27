import cv2
import numpy as np


# ============================================================
# RETINEX-BASED LOW-LIGHT IMAGE ENHANCEMENT
#
# Implements:
#   1. Single-Scale Retinex (SSR)
#   2. Multi-Scale Retinex (MSR)
#
# The enhancement is performed mainly on image luminance
# so that the original RGB color relationships are preserved.
# ============================================================


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def percentile_normalize(
    image,
    low_percentile=1.0,
    high_percentile=99.0
):
    """
    Normalize a floating-point image using percentile
    clipping.

    This prevents a few extreme pixels from controlling
    the entire output range.
    """

    image = image.astype(np.float32)

    low_value = np.percentile(
        image,
        low_percentile
    )

    high_value = np.percentile(
        image,
        high_percentile
    )

    if high_value - low_value < 1e-6:

        return np.zeros_like(
            image,
            dtype=np.float32
        )

    normalized = (
        image - low_value
    ) / (
        high_value - low_value
    )

    return np.clip(
        normalized,
        0.0,
        1.0
    )


def smooth_image(
    image,
    sigma
):
    """
    Gaussian smoothing used to estimate
    surrounding illumination.
    """

    return cv2.GaussianBlur(
        image,
        (0, 0),
        sigmaX=sigma,
        sigmaY=sigma
    )


# ============================================================
# SINGLE-SCALE RETINEX
# ============================================================

def single_scale_retinex(
    image,
    sigma=80
):
    """
    Single-Scale Retinex.

    SSR(x,y) =
        log(I(x,y)) -
        log(G_sigma * I(x,y))

    Parameters
    ----------
    image : float image in [0,1]
    sigma : Gaussian surround scale

    Returns
    -------
    SSR response
    """

    image = np.clip(
        image.astype(np.float32),
        0.0,
        1.0
    )

    # Avoid log(0)
    image_safe = image + 1e-6

    # Estimate surrounding illumination
    illumination = smooth_image(
        image_safe,
        sigma
    )

    illumination = illumination + 1e-6

    # Retinex equation
    ssr = (
        np.log(image_safe)
        -
        np.log(illumination)
    )

    return ssr


# ============================================================
# MULTI-SCALE RETINEX
# ============================================================

def multi_scale_retinex(
    image,
    sigmas=(15, 80, 250)
):
    """
    Multi-Scale Retinex.

    MSR = sum(w_i * SSR_i)

    Multiple scales allow the method to respond to
    illumination changes at different spatial sizes.
    """

    result = np.zeros_like(
        image,
        dtype=np.float32
    )

    weight = 1.0 / len(sigmas)

    for sigma in sigmas:

        ssr = single_scale_retinex(
            image,
            sigma
        )

        result += (
            weight * ssr
        )

    return result


# ============================================================
# LUMINANCE EXTRACTION
# ============================================================

def get_luminance(
    image_rgb
):
    """
    Convert RGB image to LAB and return its luminance
    channel normalized to [0,1].
    """

    lab = cv2.cvtColor(
        image_rgb,
        cv2.COLOR_RGB2LAB
    )

    luminance = (
        lab[:, :, 0].astype(np.float32)
        / 255.0
    )

    return luminance


# ============================================================
# SSR LUMINANCE ENHANCEMENT
# ============================================================

def enhance_ssr(
    luminance,
    sigma=80
):
    """
    Enhance luminance using Single-Scale Retinex.

    The Retinex response is blended with the original
    luminance to keep the enhancement natural.
    """

    ssr = single_scale_retinex(
        luminance,
        sigma
    )

    # Controlled normalization
    ssr_normalized = percentile_normalize(
        ssr,
        low_percentile=2,
        high_percentile=98
    )

    # Blend with original luminance.
    # More original information is retained to reduce
    # over-enhancement.
    enhanced = (
        0.45 * luminance
        +
        0.55 * ssr_normalized
    )

    # Gentle gamma correction.
    # Values below 1 brighten darker regions gradually.
    enhanced = np.power(
        np.clip(
            enhanced,
            0.0,
            1.0
        ),
        0.94
    )

    return np.clip(
        enhanced,
        0.0,
        1.0
    )


# ============================================================
# MSR LUMINANCE ENHANCEMENT
# ============================================================

def enhance_msr(
    luminance,
    sigmas=(15, 80, 250)
):
    """
    Enhance luminance using Multi-Scale Retinex.
    """

    msr = multi_scale_retinex(
        luminance,
        sigmas
    )

    # More conservative percentile range
    msr_normalized = percentile_normalize(
        msr,
        low_percentile=2,
        high_percentile=98
    )

    # Blend MSR with original luminance.
    enhanced = (
        0.40 * luminance
        +
        0.60 * msr_normalized
    )

    # Gentle brightness adjustment
    enhanced = np.power(
        np.clip(
            enhanced,
            0.0,
            1.0
        ),
        0.96
    )

    return np.clip(
        enhanced,
        0.0,
        1.0
    )


# ============================================================
# COLOR RECONSTRUCTION
# ============================================================

def reconstruct_image(
    original_rgb,
    enhanced_luminance
):
    """
    Replace only the LAB luminance channel.

    This preserves the chromatic information of the
    original image better than independently enhancing
    R, G and B channels.
    """

    lab = cv2.cvtColor(
        original_rgb,
        cv2.COLOR_RGB2LAB
    )

    # Convert normalized luminance to OpenCV LAB range
    new_l = (
        np.clip(
            enhanced_luminance,
            0.0,
            1.0
        )
        * 255.0
    ).astype(np.uint8)

    lab[:, :, 0] = new_l

    enhanced_rgb = cv2.cvtColor(
        lab,
        cv2.COLOR_LAB2RGB
    )

    return enhanced_rgb


# ============================================================
# ILLUMINATION MAP
# ============================================================

def get_illumination_map(
    image_rgb,
    sigma=80
):
    """
    Estimate and visualize the illumination component.
    """

    luminance = get_luminance(
        image_rgb
    )

    illumination = smooth_image(
        luminance,
        sigma
    )

    illumination = percentile_normalize(
        illumination,
        1,
        99
    )

    return (
        illumination * 255.0
    ).astype(np.uint8)


# ============================================================
# RETINEX RESPONSE VISUALIZATION
# ============================================================

def get_retinex_response(
    image_rgb,
    method="MSR"
):
    """
    Generate a grayscale visualization of the
    Retinex response.
    """

    luminance = get_luminance(
        image_rgb
    )

    method = method.upper()

    if method == "SSR":

        response = single_scale_retinex(
            luminance,
            sigma=80
        )

    else:

        response = multi_scale_retinex(
            luminance,
            sigmas=(15, 80, 250)
        )

    response = percentile_normalize(
        response,
        2,
        98
    )

    return (
        response * 255.0
    ).astype(np.uint8)


# ============================================================
# MAIN RETINEX FUNCTION
# ============================================================

def enhance_image(
    image_rgb,
    method="MSR"
):
    """
    Main enhancement function used by Flask.

    Parameters
    ----------
    image_rgb : uint8 RGB image
    method    : SSR or MSR

    Returns
    -------
    enhanced
        Enhanced RGB image.

    illumination
        Illumination map.

    response
        Retinex response visualization.
    """

    method = method.upper()

    # Extract luminance
    luminance = get_luminance(
        image_rgb
    )

    # --------------------------------------------------------
    # SSR
    # --------------------------------------------------------

    if method == "SSR":

        enhanced_luminance = enhance_ssr(
            luminance,
            sigma=80
        )

    # --------------------------------------------------------
    # MSR
    # --------------------------------------------------------

    else:

        method = "MSR"

        enhanced_luminance = enhance_msr(
            luminance,
            sigmas=(15, 80, 250)
        )

    # --------------------------------------------------------
    # Reconstruct color image
    # --------------------------------------------------------

    enhanced = reconstruct_image(
        image_rgb,
        enhanced_luminance
    )

    # --------------------------------------------------------
    # Generate visual outputs
    # --------------------------------------------------------

    illumination = get_illumination_map(
        image_rgb,
        sigma=80
    )

    response = get_retinex_response(
        image_rgb,
        method
    )

    return (
        enhanced,
        illumination,
        response
    )