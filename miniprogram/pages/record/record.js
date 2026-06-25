const app = getApp()
const recorderManager = wx.getRecorderManager()

Page({
  data: {
    isRecording: false,
    isPaused: false,
    duration: 0,
    durationText: '00:00',
    tempFilePath: '',
    resultText: '',
    language: 'auto',
    currentLang: '自动检测',
    languages: [],
    uploading: false
  },

  onLoad() {
    this.loadLanguages()
    this.initRecorder()
  },

  loadLanguages() {
    wx.request({
      url: app.globalData.baseUrl + '/languages',
      success: (res) => {
        const list = Object.entries(res.data).map(([key, val]) => ({
          code: key,
          name: val
        }))
        this.setData({ languages: list })
      }
    })
  },

  initRecorder() {
    recorderManager.onStop((res) => {
      this.setData({
        tempFilePath: res.tempFilePath,
        isRecording: false,
        isPaused: false
      })
    })

    recorderManager.onError((err) => {
      wx.showToast({ title: '录音失败', icon: 'error' })
      this.setData({ isRecording: false })
    })
  },

  changeLanguage(e) {
    const idx = e.detail.value
    const lang = this.data.languages[idx]
    this.setData({ language: lang.code, currentLang: lang.name })
  },

  startRecord() {
    this.setData({ isRecording: true, isPaused: false, duration: 0, durationText: '00:00', resultText: '', tempFilePath: '' })
    this._timer = setInterval(() => {
      const d = this.data.duration + 1
      this.setData({ duration: d, durationText: this.formatTime(d) })
    }, 1000)

    recorderManager.start({
      duration: 300000,
      sampleRate: 16000,
      numberOfChannels: 1,
      format: 'mp3'
    })
  },

  pauseRecord() {
    recorderManager.pause()
    clearInterval(this._timer)
    this.setData({ isPaused: true })
  },

  resumeRecord() {
    recorderManager.resume()
    this._timer = setInterval(() => {
      const d = this.data.duration + 1
      this.setData({ duration: d, durationText: this.formatTime(d) })
    }, 1000)
    this.setData({ isPaused: false })
  },

  stopRecord() {
    clearInterval(this._timer)
    recorderManager.stop()
  },

  chooseAudio() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac'],
      success: (res) => {
        const file = res.tempFiles[0]
        this.setData({
          tempFilePath: file.path,
          resultText: '',
          durationText: this.formatTime(file.size > 0 ? 0 : 0)
        })
        wx.showToast({ title: '已选择文件', icon: 'success' })
      }
    })
  },

  transcribe() {
    if (!this.data.tempFilePath) {
      wx.showToast({ title: '请先录音', icon: 'none' })
      return
    }
    this.setData({ uploading: true })
    wx.uploadFile({
      url: app.globalData.baseUrl + '/transcribe',
      filePath: this.data.tempFilePath,
      name: 'file',
      formData: { language: this.data.language },
      success: (res) => {
        const data = JSON.parse(res.data)
        this.setData({ resultText: data.text, uploading: false })
      },
      fail: () => {
        wx.showToast({ title: '识别失败', icon: 'error' })
        this.setData({ uploading: false })
      }
    })
  },

  copyText() {
    if (!this.data.resultText) return
    wx.setClipboardData({
      data: this.data.resultText,
      success: () => wx.showToast({ title: '已复制', icon: 'success' })
    })
  },

  playAudio() {
    if (!this.data.tempFilePath) return
    const audio = wx.createInnerAudioContext()
    audio.src = this.data.tempFilePath
    audio.play()
  },

  formatTime(sec) {
    const m = Math.floor(sec / 60).toString().padStart(2, '0')
    const s = (sec % 60).toString().padStart(2, '0')
    return m + ':' + s
  },

  resetAudio() {
    this.setData({ tempFilePath: '', resultText: '' })
  }
})
