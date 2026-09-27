from flask import (
    Flask,
    render_template,
    request,
    send_from_directory
)

from werkzeug.utils import secure_filename

import os
import cv2
import numpy as np
import time

from dcp import enhance_image


app = Flask(__name__)


# ==========================================
# FOLDERS
# ==========================================

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULT_FOLDER"] = RESULT_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    RESULT_FOLDER,
    exist_ok=True
)


# ==========================================
# IMAGE TYPES
# ==========================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


def allowed_file(filename):

    return (
        "."
        in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================================
# IMAGE METRICS
# ==========================================

def calculate_brightness(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    return float(
        np.mean(gray)
    )


def calculate_contrast(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    return float(
        np.std(gray)
    )


def calculate_entropy(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    histogram = cv2.calcHist(
        [gray],
        [0],
        None,
        [256],
        [0, 256]
    ).flatten()

    total = np.sum(
        histogram
    )

    if total == 0:

        return 0.0

    probabilities = (
        histogram / total
    )

    probabilities = probabilities[
        probabilities > 0
    ]

    entropy = -np.sum(
        probabilities
        *
        np.log2(probabilities)
    )

    return float(
        entropy
    )


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# ENHANCE IMAGE
# ==========================================

@app.route(
    "/enhance",
    methods=["POST"]
)
def enhance():

    # Check image
    if "image" not in request.files:

        return render_template(
            "index.html",
            error="Please select an image."
        )

    file = request.files["image"]

    if file.filename == "":

        return render_template(
            "index.html",
            error="Please select an image."
        )

    # Check extension
    if not allowed_file(
        file.filename
    ):

        return render_template(
            "index.html",
            error="Unsupported image format."
        )

    # Get selected method
    method = request.form.get(
        "method",
        "MSR"
    ).upper()

    if method not in {
        "SSR",
        "MSR"
    }:

        method = "MSR"

    # Secure filename
    filename = secure_filename(
        file.filename
    )

    if not filename:

        return render_template(
            "index.html",
            error="Invalid filename."
        )

    # Save uploaded image
    upload_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(
        upload_path
    )

    # Read image
    image = cv2.imread(
        upload_path
    )

    if image is None:

        return render_template(
            "index.html",
            error="Could not read image."
        )

    # BGR -> RGB
    image_rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # ======================================
    # ORIGINAL METRICS
    # ======================================

    brightness_before = (
        calculate_brightness(
            image_rgb
        )
    )

    contrast_before = (
        calculate_contrast(
            image_rgb
        )
    )

    entropy_before = (
        calculate_entropy(
            image_rgb
        )
    )

    # ======================================
    # RETINEX
    # ======================================

    start_time = time.perf_counter()

    (
        enhanced,
        illumination,
        response
    ) = enhance_image(
        image_rgb,
        method
    )

    processing_time = (
        time.perf_counter()
        -
        start_time
    )

    # ======================================
    # ENHANCED METRICS
    # ======================================

    brightness_after = (
        calculate_brightness(
            enhanced
        )
    )

    contrast_after = (
        calculate_contrast(
            enhanced
        )
    )

    entropy_after = (
        calculate_entropy(
            enhanced
        )
    )

    # ======================================
    # FILENAMES
    # ======================================

    base_name, extension = (
        os.path.splitext(
            filename
        )
    )

    original_filename = (
        "original_"
        + base_name
        + extension
    )

    enhanced_filename = (
        method.lower()
        + "_enhanced_"
        + base_name
        + extension
    )

    illumination_filename = (
        "illumination_"
        + base_name
        + ".png"
    )

    response_filename = (
        method.lower()
        + "_response_"
        + base_name
        + extension
    )

    # ======================================
    # SAVE ORIGINAL
    # ======================================

    cv2.imwrite(
        os.path.join(
            RESULT_FOLDER,
            original_filename
        ),
        cv2.cvtColor(
            image_rgb,
            cv2.COLOR_RGB2BGR
        )
    )

    # ======================================
    # SAVE ENHANCED
    # ======================================

    cv2.imwrite(
        os.path.join(
            RESULT_FOLDER,
            enhanced_filename
        ),
        cv2.cvtColor(
            enhanced,
            cv2.COLOR_RGB2BGR
        )
    )

    # ======================================
    # SAVE ILLUMINATION
    # ======================================

    cv2.imwrite(
        os.path.join(
            RESULT_FOLDER,
            illumination_filename
        ),
        illumination
    )

    # ======================================
    # SAVE RETINEX RESPONSE
    # ======================================

    cv2.imwrite(
        os.path.join(
            RESULT_FOLDER,
            response_filename
        ),
        cv2.cvtColor(
            response,
            cv2.COLOR_RGB2BGR
        )
    )

    # ======================================
    # METRIC CHANGE
    # ======================================

    if contrast_before > 0:

        contrast_change = (
            (
                contrast_after
                -
                contrast_before
            )
            /
            contrast_before
        ) * 100

    else:

        contrast_change = 0

    # ======================================
    # SHOW RESULTS
    # ======================================

    return render_template(
        "index.html",

        original_image=(
            "/results/"
            + original_filename
        ),

        enhanced_image=(
            "/results/"
            + enhanced_filename
        ),

        illumination_image=(
            "/results/"
            + illumination_filename
        ),

        response_image=(
            "/results/"
            + response_filename
        ),

        method=method,

        brightness_before=round(
            brightness_before,
            2
        ),

        brightness_after=round(
            brightness_after,
            2
        ),

        contrast_before=round(
            contrast_before,
            2
        ),

        contrast_after=round(
            contrast_after,
            2
        ),

        contrast_change=round(
            contrast_change,
            2
        ),

        entropy_before=round(
            entropy_before,
            2
        ),

        entropy_after=round(
            entropy_after,
            2
        ),

        processing_time=round(
            processing_time,
            3
        )
    )


# ==========================================
# SERVE RESULTS
# ==========================================

@app.route(
    "/results/<filename>"
)
def result_file(filename):

    return send_from_directory(
        RESULT_FOLDER,
        filename
    )


# ==========================================
# DOWNLOAD
# ==========================================

@app.route(
    "/download/<filename>"
)
def download_file(filename):

    return send_from_directory(
        RESULT_FOLDER,
        filename,
        as_attachment=True
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )