<template>
  <div v-if="ready">
    <header class="page-hero article-head">
      <div>
        <h1 class="page-title">编辑笔记</h1>
        <p class="page-lead">{{ meta.title || path }} · 粘贴或上传图片</p>
      </div>
      <div class="row">
        <button @click="onUploadClick">上传图片</button>
        <input ref="fileInput" type="file" accept="image/*" hidden @change="onFile" />
        <button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
        <RouterLink :to="`/page/${path}`"><button>预览页</button></RouterLink>
      </div>
    </header>

    <div class="card row">
      <label>状态
        <select v-model="meta.status">
          <option value="todo">todo</option>
          <option value="reading">reading</option>
          <option value="done">done</option>
          <option value="abandoned">abandoned</option>
        </select>
      </label>
      <label>检索分 <input v-model="meta.score" style="width:4rem" /></label>
      <label>个人分 <input v-model="meta.rating" style="width:4rem" placeholder="1–10" /></label>
      <label>入库 <input v-model="meta.added_at" style="width:8rem" /></label>
      <label style="flex:1;min-width:14rem">摘要 <input v-model="meta.summary" placeholder="一句话摘要" /></label>
      <label>标签 <input v-model="tagsText" placeholder="llm, reasoning" style="width:12rem" /></label>
    </div>

    <div class="editor-shell">
      <div class="editor-pane" ref="editorHost"></div>
      <div class="preview-pane prose" v-html="previewHtml"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { markdown } from '@codemirror/lang-markdown'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { getPage, savePage, uploadImage } from '../api'

const props = defineProps({ path: { type: String, required: true } })
const ready = ref(false)
const saving = ref(false)
const meta = reactive({})
const tagsText = ref('')
const body = ref('')
const editorHost = ref(null)
const fileInput = ref(null)
let view = null

const previewHtml = computed(() =>
  DOMPurify.sanitize(marked.parse(body.value || '')),
)

async function load() {
  const data = await getPage(props.path)
  Object.keys(meta).forEach((k) => delete meta[k])
  Object.assign(meta, data.meta || {})
  if (!meta.status) meta.status = 'todo'
  tagsText.value = Array.isArray(meta.tags) ? meta.tags.join(', ') : (meta.tags || '')
  body.value = data.body || ''
  ready.value = true
  requestAnimationFrame(mountEditor)
}

function mountEditor() {
  if (!editorHost.value) return
  if (view) {
    view.destroy()
    view = null
  }
  view = new EditorView({
    doc: body.value,
    extensions: [
      basicSetup,
      markdown(),
      EditorView.theme({
        '&': { backgroundColor: '#fff', color: '#1a2332' },
        '.cm-content': { fontFamily: '"IBM Plex Mono", ui-monospace, monospace', fontSize: '13.5px' },
        '.cm-gutters': { backgroundColor: '#f4f7fa', color: '#5c6b7a', border: 'none' },
      }),
      EditorView.updateListener.of((u) => {
        if (u.docChanged) body.value = u.state.doc.toString()
      }),
      EditorView.domEventHandlers({
        paste(event) {
          const items = event.clipboardData?.items
          if (!items) return
          for (const item of items) {
            if (item.type.startsWith('image/')) {
              event.preventDefault()
              const file = item.getAsFile()
              if (file) insertUploaded(file)
              return true
            }
          }
        },
        drop(event) {
          const file = event.dataTransfer?.files?.[0]
          if (file && file.type.startsWith('image/')) {
            event.preventDefault()
            insertUploaded(file)
            return true
          }
        },
      }),
    ],
    parent: editorHost.value,
  })
}

async function insertUploaded(file) {
  const res = await uploadImage(file)
  const md = `\n![](${res.url})\n`
  if (!view) {
    body.value += md
    return
  }
  const pos = view.state.selection.main.head
  view.dispatch({
    changes: { from: pos, insert: md },
    selection: { anchor: pos + md.length },
  })
  body.value = view.state.doc.toString()
}

function onUploadClick() {
  fileInput.value?.click()
}

function onFile(e) {
  const file = e.target.files?.[0]
  if (file) insertUploaded(file)
  e.target.value = ''
}

async function save() {
  saving.value = true
  try {
    meta.tags = tagsText.value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
    await savePage(props.path, { meta: { ...meta }, body: body.value })
  } finally {
    saving.value = false
  }
}

onMounted(load)
watch(() => props.path, load)
onBeforeUnmount(() => {
  if (view) view.destroy()
})
</script>
