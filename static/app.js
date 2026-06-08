const fileInput = document.getElementById("file-input");
const imagePreview = document.getElementById("image-preview");
const dropZone = document.getElementById("drop-zone");
const dropLabel = document.getElementById("drop-label");

let imageBase64 = "";
let imageMediaType = "";

function handleFile(file) {
    if (!file) return;

    imageMediaType = file.type;

    const reader = new FileReader();
    reader.onload = (e) => {
        // split pour enlever le préfixe "data:image/jpeg;base64,"
        imageBase64 = e.target.result.split(",")[1];
        imagePreview.src = e.target.result;
        imagePreview.classList.add("visible");
        dropLabel.textContent = file.name.toUpperCase();
    };
    reader.readAsDataURL(file);
}

dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => handleFile(e.target.files[0]));

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    handleFile(e.dataTransfer.files[0]);
});

document.addEventListener("htmx:afterSwap", (e) => {
    if (e.detail.target.id !== "form-container") return;

    const hiddenData = document.querySelector('input[name="image_data"]');
    const hiddenType = document.querySelector('input[name="image_media_type"]');

    if (hiddenData) hiddenData.value = imageBase64;
    if (hiddenType) hiddenType.value = imageMediaType;
});

// HTMX ne swap pas sur les 4xx/5xx par défaut
document.addEventListener("htmx:responseError", (e) => {
    if (e.detail.target) e.detail.target.innerHTML = e.detail.xhr.responseText;
});

window.resetApp = function () {
    document.getElementById("form-container").innerHTML = "";
    document.getElementById("confirmation-container").innerHTML = "";
    imagePreview.classList.remove("visible");
    imagePreview.src = "";
    fileInput.value = "";
    dropLabel.textContent = "DROP ZONE — CLIQUER OU GLISSER";
    imageBase64 = "";
    imageMediaType = "";
};