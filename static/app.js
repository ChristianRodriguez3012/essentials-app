const state = {
  view: "grid",
  audioFile: null,
  imageFile: null,
  visibility: "private",
  container: "mp4",
  resolution: "1080p",
};

const gridView = document.getElementById("grid-view");
const workspaceView = document.getElementById("workspace-view");
const activeModule = document.getElementById("active-module");
const statusText = document.getElementById("status-text");
const renderProgress = document.getElementById("render-progress");
const uploadProgress = document.getElementById("upload-progress");
const waveformPlaceholder = document.getElementById("waveform-placeholder");

function setStatus(text) {
  statusText.textContent = text;
}

function switchView(view) {
  state.view = view;
  const showWorkspace = view === "workspace";
  gridView.classList.toggle("hidden", showWorkspace);
  workspaceView.classList.toggle("hidden", !showWorkspace);
  activeModule.classList.toggle("hidden", !showWorkspace);
}

function setGroupSelection(selector, currentValue) {
  document.querySelectorAll(selector).forEach((button) => {
    const active = button.dataset.value === currentValue;
    button.classList.toggle("border-[#FF3B30]", active);
    button.classList.toggle("drop-glow", active);
  });
}

function bindDropZone(zoneId, labelId, accept, onFile) {
  const zone = document.getElementById(zoneId);
  const label = document.getElementById(labelId);

  ["dragenter", "dragover"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("active");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("active");
    });
  });

  zone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (!file) return;

    const valid = accept.some((suffix) => file.name.toLowerCase().endsWith(suffix));
    if (!valid) {
      setStatus("Estado: Archivo inválido");
      return;
    }

    label.textContent = file.name;
    onFile(file);
  });

  zone.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = accept.join(",");
    input.onchange = () => {
      const file = input.files?.[0];
      if (!file) return;
      label.textContent = file.name;
      onFile(file);
    };
    input.click();
  });
}

function animateProgress(element, value) {
  element.style.width = `${value}%`;
}

async function handleRenderAndUpload() {
  if (!state.audioFile || !state.imageFile) {
    setStatus("Estado: Adjunta audio e imagen");
    return;
  }

  const titleInput = document.getElementById("title");
  const descriptionInput = document.getElementById("description");
  const tagsInput = document.getElementById("tags");
  const autoBgInput = document.getElementById("auto-bg");

  const form = new FormData();
  form.append("audio", state.audioFile);
  form.append("image", state.imageFile);
  form.append("title", titleInput.value.trim() || "Untitled Upload");
  form.append("description", descriptionInput.value);
  form.append("tags", tagsInput.value);
  form.append("visibility", state.visibility);
  form.append("container", state.container);
  form.append("resolution", state.resolution);
  form.append("auto_black_bg", autoBgInput.checked ? "true" : "false");
  form.append("mock_upload", "true");

  setStatus("Estado: Renderizando con FFmpeg...");
  animateProgress(renderProgress, 10);

  const renderAnimation = setInterval(() => {
    const current = parseInt(renderProgress.style.width || "0", 10);
    if (current < 90) animateProgress(renderProgress, current + 10);
  }, 250);

  try {
    const response = await fetch("/api/render-and-upload", {
      method: "POST",
      body: form,
    });

    clearInterval(renderAnimation);
    animateProgress(renderProgress, 100);

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Render/upload failed");
    }

    setStatus("Estado: Subiendo a API...");
    for (let i = 20; i <= 100; i += 20) {
      await new Promise((resolve) => setTimeout(resolve, 120));
      animateProgress(uploadProgress, i);
    }

    const data = await response.json();
    setStatus(`Estado: Listo · Video ID ${data.video_id}`);
  } catch (error) {
    setStatus(`Estado: Error - ${error.message}`);
  }
}

function init() {
  document.getElementById("drop-card").addEventListener("click", () => switchView("workspace"));
  document.getElementById("back-to-grid").addEventListener("click", () => switchView("grid"));

  bindDropZone("audio-drop", "audio-label", [".wav"], (file) => {
    state.audioFile = file;
    waveformPlaceholder.classList.remove("hidden");
    document.getElementById("title").value = file.name.replace(/\.[^/.]+$/, "");
  });

  bindDropZone("image-drop", "image-label", [".png", ".jpg", ".jpeg"], (file) => {
    state.imageFile = file;
  });

  document.querySelectorAll(".visibility-btn").forEach((button) => {
    button.addEventListener("click", () => {
      state.visibility = button.dataset.value;
      setGroupSelection(".visibility-btn", state.visibility);
    });
  });

  document.querySelectorAll(".container-btn").forEach((button) => {
    button.addEventListener("click", () => {
      state.container = button.dataset.value;
      setGroupSelection(".container-btn", state.container);
    });
  });

  document.querySelectorAll(".resolution-btn").forEach((button) => {
    button.addEventListener("click", () => {
      state.resolution = button.dataset.value;
      setGroupSelection(".resolution-btn", state.resolution);
    });
  });

  setGroupSelection(".visibility-btn", state.visibility);
  setGroupSelection(".container-btn", state.container);
  setGroupSelection(".resolution-btn", state.resolution);

  document.getElementById("render-upload").addEventListener("click", handleRenderAndUpload);
}

init();
