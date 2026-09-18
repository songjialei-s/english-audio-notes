const { createApp, ref, onMounted } = Vue

const API = window.location.origin

createApp({
    setup() {
        const tab = ref('pdf')
        const voiceId = ref('zh-female')
        const rate = ref(100)
        const language = ref('auto')
        const voices = ref([])
        const languages = ref({})
        const pdfLoading = ref(false)
        const pdfResult = ref(null)
        const transcribeLoading = ref(false)
        const transcribeResult = ref('')
        const historyList = ref([])

        const loadVoices = async () => {
            const res = await fetch(`${API}/api/voices`)
            voices.value = await res.json()
        }

        const loadLanguages = async () => {
            const res = await fetch(`${API}/api/languages`)
            languages.value = await res.json()
        }

        const loadHistory = async () => {
            const res = await fetch(`${API}/api/history`)
            historyList.value = await res.json()
        }

        const handlePdf = async (e) => {
            const file = e.target.files[0]
            if (!file) return
            await uploadPdf(file)
        }

        const handlePdfDrop = async (e) => {
            const file = e.dataTransfer.files[0]
            if (!file || !file.name.endsWith('.pdf')) return
            await uploadPdf(file)
        }

        const uploadPdf = async (file) => {
            pdfLoading.value = true
            pdfResult.value = null
            const formData = new FormData()
            formData.append('file', file)
            formData.append('voice_id', voiceId.value)
            formData.append('rate', rate.value)
            try {
                const res = await fetch(`${API}/api/upload-pdf`, { method: 'POST', body: formData })
                pdfResult.value = await res.json()
            } catch (err) {
                alert('上传失败: ' + err.message)
            }
            pdfLoading.value = false
        }

        const handleMedia = async (e) => {
            const file = e.target.files[0]
            if (!file) return
            await uploadMedia(file)
        }

        const handleMediaDrop = async (e) => {
            const file = e.dataTransfer.files[0]
            if (!file) return
            await uploadMedia(file)
        }

        const uploadMedia = async (file) => {
            transcribeLoading.value = true
            transcribeResult.value = ''
            const formData = new FormData()
            formData.append('file', file)
            formData.append('language', language.value)
            try {
                const res = await fetch(`${API}/api/transcribe`, { method: 'POST', body: formData })
                const data = await res.json()
                transcribeResult.value = data.text || ''
                loadHistory()
            } catch (err) {
                alert('识别失败: ' + err.message)
            }
            transcribeLoading.value = false
        }

        const copyText = () => {
            navigator.clipboard.writeText(transcribeResult.value)
            alert('已复制')
        }

        const deleteHistory = async (id) => {
            if (!confirm('确定删除？')) return
            await fetch(`${API}/api/history/${id}`, { method: 'DELETE' })
            loadHistory()
        }

        onMounted(() => {
            loadVoices()
            loadLanguages()
        })

        return {
            tab, voiceId, rate, language,
            voices, languages,
            pdfLoading, pdfResult,
            transcribeLoading, transcribeResult,
            historyList,
            handlePdf, handlePdfDrop,
            handleMedia, handleMediaDrop,
            copyText, loadHistory, deleteHistory
        }
    }
}).mount('#app')
