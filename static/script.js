/* ==========================================
   IMAGE ELEMENTS
========================================== */

const imageInput =
    document.getElementById(
        "imageInput"
    );

const dropZone =
    document.getElementById(
        "dropZone"
    );

const previewContainer =
    document.getElementById(
        "previewContainer"
    );

const previewImage =
    document.getElementById(
        "previewImage"
    );

const fileName =
    document.getElementById(
        "fileName"
    );

const removeImage =
    document.getElementById(
        "removeImage"
    );

const uploadForm =
    document.getElementById(
        "uploadForm"
    );

const enhanceButton =
    document.getElementById(
        "enhanceButton"
    );


/* ==========================================
   METHOD SELECTOR
========================================== */

const methodOptions =
    document.querySelectorAll(
        ".method-option"
    );


methodOptions.forEach(
    function (option) {

        const radio =
            option.querySelector(
                "input"
            );


        radio.addEventListener(
            "change",
            function () {

                methodOptions.forEach(
                    function (item) {

                        item.classList.remove(
                            "active"
                        );

                    }
                );


                option.classList.add(
                    "active"
                );

            }
        );

    }
);


/* ==========================================
   IMAGE PREVIEW
========================================== */

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            if (
                this.files &&
                this.files.length > 0
            ) {

                showPreview(
                    this.files[0]
                );

            }

        }
    );

}


function showPreview(file) {

    if (!previewContainer) {
        return;
    }


    fileName.textContent =
        file.name;


    const reader =
        new FileReader();


    reader.onload =
        function (event) {

            previewImage.src =
                event.target.result;

            previewContainer.classList.add(
                "visible"
            );

        };


    reader.readAsDataURL(
        file
    );

}


/* ==========================================
   REMOVE IMAGE
========================================== */

if (removeImage) {

    removeImage.addEventListener(
        "click",
        function (event) {

            event.preventDefault();

            imageInput.value = "";

            previewImage.src = "";

            fileName.textContent = "";

            previewContainer.classList.remove(
                "visible"
            );

        }
    );

}


/* ==========================================
   DRAG AND DROP
========================================== */

if (dropZone) {

    dropZone.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            dropZone.classList.add(
                "dragging"
            );

        }
    );


    dropZone.addEventListener(
        "dragenter",
        function (event) {

            event.preventDefault();

            dropZone.classList.add(
                "dragging"
            );

        }
    );


    dropZone.addEventListener(
        "dragleave",
        function () {

            dropZone.classList.remove(
                "dragging"
            );

        }
    );


    dropZone.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            dropZone.classList.remove(
                "dragging"
            );


            const files =
                event.dataTransfer.files;


            if (
                files &&
                files.length > 0
            ) {

                imageInput.files =
                    files;

                showPreview(
                    files[0]
                );

            }

        }
    );

}


/* ==========================================
   PROCESSING
========================================== */

if (uploadForm) {

    uploadForm.addEventListener(
        "submit",
        function () {

            if (enhanceButton) {

                enhanceButton.disabled =
                    true;


                enhanceButton.innerHTML = `
                    <span>
                        Enhancing image...
                    </span>

                    <span>
                        ◌
                    </span>
                `;

            }

        }
    );

}


/* ==========================================
   BEFORE / AFTER SLIDER
========================================== */

const comparisonSlider =
    document.getElementById(
        "comparisonSlider"
    );

const beforeImageContainer =
    document.getElementById(
        "beforeImageContainer"
    );

const sliderLine =
    document.getElementById(
        "sliderLine"
    );

const sliderHandle =
    document.getElementById(
        "sliderHandle"
    );


if (comparisonSlider) {

    let isDragging = false;


    function moveSlider(clientX) {

        const rect =
            comparisonSlider.getBoundingClientRect();


        let position =
            (
                (clientX - rect.left)
                /
                rect.width
            ) * 100;


        position =
            Math.max(
                0,
                Math.min(
                    100,
                    position
                )
            );


        if (beforeImageContainer) {

            beforeImageContainer.style.width =
                position + "%";

        }


        if (sliderLine) {

            sliderLine.style.left =
                position + "%";

        }


        if (sliderHandle) {

            sliderHandle.style.left =
                position + "%";

        }

    }


    comparisonSlider.addEventListener(
        "mousedown",
        function (event) {

            isDragging = true;

            moveSlider(
                event.clientX
            );

        }
    );


    document.addEventListener(
        "mousemove",
        function (event) {

            if (isDragging) {

                moveSlider(
                    event.clientX
                );

            }

        }
    );


    document.addEventListener(
        "mouseup",
        function () {

            isDragging = false;

        }
    );


    comparisonSlider.addEventListener(
        "touchstart",
        function (event) {

            isDragging = true;


            if (
                event.touches.length > 0
            ) {

                moveSlider(
                    event.touches[0].clientX
                );

            }

        },
        { passive: true }
    );


    comparisonSlider.addEventListener(
        "touchmove",
        function (event) {

            if (
                isDragging &&
                event.touches.length > 0
            ) {

                moveSlider(
                    event.touches[0].clientX
                );

            }

        },
        { passive: true }
    );


    comparisonSlider.addEventListener(
        "touchend",
        function () {

            isDragging = false;

        }
    );


    /* Initial position = 50% */

    const rect =
        comparisonSlider.getBoundingClientRect();


    moveSlider(
        rect.left +
        rect.width * 0.5
    );

}