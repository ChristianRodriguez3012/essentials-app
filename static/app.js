const state = {
  audioFile: null,
  imageFile: null,
  privacy: 'private',
  container: 'mp4',
  resolution: '1080p',
  renderProgress: 0,
  uploadProgress: 0,
  progressTimer: null,
}

const $ = (id) => document.getElementById(id)

const gridView = $('gridView')
const workspaceView = $('workspaceView')
const statusText = $('statusText')
const titleInput = $('titleInput')

function showGrid() {
  gridView.classList.remove('hidden')
  workspaceView.classList.add('hidden')
}

function showWorkspace() {
  gridView.classList.add('hidden')
  workspaceView.classList.remove('hidden')
}

function setStatus(text) {
  statusText.textContent = `Estado: ${text}`
}

function setProgress(render, upload) {
  $('renderBar').style.width = `${render}%`
  $('uploadBar').style.width = `${upload}%`
}

function bindDropZone(zoneId, labelId, fileHandler, acceptExts) {
  const zone = $(zoneId)
  const label = $(labelId)

  const setDragState = (active) => {
    zone.classList.toggle('border-neon', active)
  }

  zone.addEventListener('dragover', (e) => {
    e.preventDefault()
    setDragState(true)
  })

  zone.addEventListener('dragleave', () => setDragState(false))

  zone.addEventListener('drop', (e) => {
    e.preventDefault()
    setDragState(false)
    const file = e.dataTransfer?.files?.[0]
    if (!file) return

    const lower = file.name.toLowerCase()
    if (!acceptExts.some((ext) => lower.endsWith(ext))) {
      setStatus(`Archivo inválido: ${file.name}`)
      return
    }

    label.textContent = file.name
    fileHandler(file)
  })
}

function setupButtons() {
  document.querySelectorAll('.privacy-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.privacy = btn.dataset.value
      document.querySelectorAll('.privacy-btn').forEach((b) => {
        b.classList.remove('bg-neon/20', 'text-neon')
      })
      btn.classList.add('bg-neon/20', 'text-neon')
    })
  })

  document.querySelectorAll('.preset-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const group = btn.dataset.group
      const value = btn.dataset.value
      state[group] = value

      document.querySelectorAll(`.preset-btn[data-group="${group}"]`).forEach((b) => {
        b.classList.remove('bg-neon/20', 'text-neon')
      })
      btn.classList.add('bg-neon/20', 'text-neon')
    })
  })
}

function startVisualProgress() {
  clearInterval(state.progressTimer)
  state.renderProgress = 0
  state.uploadProgress = 0
  setProgress(0, 0)

  state.progressTimer = setInterval(() => {
    if (state.renderProgress < 92) {
      state.renderProgress += 2
    } else if (state.uploadProgress < 95) {
      state.uploadProgress += 3
    }
    setProgress(state.renderProgress, state.uploadProgress)
  }, 180)
}

function finishProgress() {
  clearInterval(state.progressTimer)
  setProgress(100, 100)
}

async function submitJob() {
  if (!state.audioFile || !state.imageFile) {
    setStatus('Carga audio e imagen antes de renderizar')
    return
  }

  const form = new FormData()
  form.append('audio', state.audioFile)
  form.append('image', state.imageFile)
  form.append('title', titleInput.value.trim() || 'Untitled Track')
  form.append('description', $('descriptionInput').value.trim())
  form.append('tags', $('tagsInput').value.trim())
  form.append('privacy_status', state.privacy)
  form.append('container', state.container)
  form.append('resolution', state.resolution)
  form.append('auto_black_background', String($('autoBlack').checked))

  setStatus('Renderizando con FFmpeg...')
  startVisualProgress()

  try {
    const response = await fetch('/api/render-and-upload', {
      method: 'POST',
      body: form,
    })

    const payload = await response.json()
    if (!response.ok) {
      throw new Error(payload.detail || 'Error inesperado')
    }

    finishProgress()
    setStatus(`Subido a YouTube (ID: ${payload.video_id || 'N/A'})`)
  } catch (error) {
    clearInterval(state.progressTimer)
    setStatus(`Fallo: ${error.message}`)
  }
}

$('dropCard').addEventListener('click', showWorkspace)
$('homeButton').addEventListener('click', showGrid)
$('renderButton').addEventListener('click', submitJob)

bindDropZone('audioDrop', 'audioLabel', (file) => {
  state.audioFile = file
  $('wavePlaceholder').classList.remove('hidden')
  if (!titleInput.value.trim()) {
    titleInput.value = file.name.replace(/\.wav$/i, '')
  }
}, ['.wav'])

bindDropZone('imageDrop', 'imageLabel', (file) => {
  state.imageFile = file
}, ['.png', '.jpg', '.jpeg'])

setupButtons()
showGrid()
setProgress(0, 0)
setStatus('Listo')
