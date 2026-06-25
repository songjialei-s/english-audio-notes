const app = getApp()
const recorderManager = wx.getRecorderManager()

Page({
  data: {
    isRecording: false,
    isPaused: false,
    isPlaying: false,
    playbackRate: 1,
    currentTime: '00:00',
    duration: 0,
    durationText: '00:00',
    tempFilePath: '',
    resultText: '',
    language: 'auto',
    currentLang: '自动检测',
    languages: [],
    uploading: false,
    historyList: [],
    showHistory: false
  },

  onLoad() {
    this.loadLanguages()
    this.initRecorder()
    this.loadHistory()
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
        this.saveToHistory(data.text)
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

  togglePlay() {
    if (this.data.isPlaying) {
      if (this._audio) {
        this._audio.stop()
        this._audio.destroy()
        this._audio = null
      }
      this.setData({ isPlaying: false })
    } else {
      this.startPlay()
    }
  },

  startPlay() {
    if (!this.data.tempFilePath) return
    this._audio = wx.createInnerAudioContext()
    this._audio.src = this.data.tempFilePath
    this._audio.playbackRate = this.data.playbackRate
    this._audio.onTimeUpdate(() => {
      if (this._audio) {
        this.setData({ currentTime: this.formatTime(Math.floor(this._audio.currentTime)) })
      }
    })
    this._audio.onEnded(() => {
      this.setData({ isPlaying: false, currentTime: '00:00' })
      this._audio = null
    })
    this._audio.play()
    this.setData({ isPlaying: true })
  },

  changeSpeed() {
    const speeds = [1, 1.5, 2, 3]
    const currentIndex = speeds.indexOf(this.data.playbackRate)
    const nextIndex = (currentIndex + 1) % speeds.length
    const newRate = speeds[nextIndex]
    this.setData({ playbackRate: newRate })
    if (this._audio) {
      this._audio.playbackRate = newRate
    }
  },

  seekForward() {
    if (this._audio) {
      this._audio.seek(this._audio.currentTime + 10)
    }
  },

  seekBackward() {
    if (this._audio) {
      const newTime = Math.max(0, this._audio.currentTime - 10)
      this._audio.seek(newTime)
    }
  },

  formatTime(sec) {
    const m = Math.floor(sec / 60).toString().padStart(2, '0')
    const s = (sec % 60).toString().padStart(2, '0')
    return m + ':' + s
  },

  resetAudio() {
    if (this._audio) {
      this._audio.stop()
      this._audio.destroy()
      this._audio = null
    }
    this.setData({ tempFilePath: '', resultText: '', isPlaying: false, playbackRate: 1, currentTime: '00:00' })
  },

  loadHistory() {
    const history = wx.getStorageSync('record_history') || []
    this.setData({ historyList: history })
  },

  saveToHistory(text) {
    if (!text) return
    let history = wx.getStorageSync('record_history') || []
    const now = new Date()
    const dateStr = `${now.getMonth()+1}/${now.getDate()} ${now.getHours()}:${String(now.getMinutes()).padStart(2,'0')}`
    const item = {
      id: Date.now(),
      date: dateStr,
      text: text,
      duration: this.data.durationText
    }
    history.unshift(item)
    if (history.length > 60) {
      history = history.slice(0, 60)
    }
    wx.setStorageSync('record_history', history)
    this.setData({ historyList: history })
  },

  toggleHistory() {
    this.setData({ showHistory: !this.data.showHistory })
  },

  viewHistory(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.historyList.find(h => h.id === id)
    if (item) {
      this.setData({ resultText: item.text, showHistory: false })
    }
  },

  deleteHistory(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条记录吗？',
      success: (res) => {
        if (res.confirm) {
          let history = this.data.historyList.filter(h => h.id !== id)
          wx.setStorageSync('record_history', history)
          this.setData({ historyList: history })
          wx.showToast({ title: '已删除', icon: 'success' })
        }
      }
    })
  },

  clearHistory() {
    wx.showModal({
      title: '清空历史',
      content: '确定要清空所有历史记录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.setStorageSync('record_history', [])
          this.setData({ historyList: [] })
          wx.showToast({ title: '已清空', icon: 'success' })
        }
      }
    })
  }
})
