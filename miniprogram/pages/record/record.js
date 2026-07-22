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
    uploadProgress: 0,
    processingText: '',
    audioDuration: 0,
    audioCurrentTime: 0,
    sliderValue: 0,
    historyList: [],
    showHistory: false,
    selectedText: '',
    isVideo: false,
    fileName: '',
    trimming: false,
    trimResult: null
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
          durationText: this.formatTime(file.size > 0 ? 0 : 0),
          fileName: file.name
        })
        wx.showToast({ title: '已选择音频', icon: 'success' })
      }
    })
  },

  chooseVideo() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp'],
      success: (res) => {
        const file = res.tempFiles[0]
        this.setData({
          tempFilePath: file.path,
          resultText: '',
          isVideo: true,
          fileName: file.name
        })
        wx.showToast({ title: '已选择视频', icon: 'success' })
      }
    })
  },

  transcribe() {
    if (!this.data.tempFilePath) {
      wx.showToast({ title: '请先录音', icon: 'none' })
      return
    }
    
    const audioDur = this.data.audioDuration || this.data.duration || 60
    const estTotal = Math.max(10, Math.ceil(audioDur * 0.4))
    
    this.setData({ uploading: true, uploadProgress: 0, processingText: '准备上传...' })
    this._processStartTime = Date.now()
    this._estTotal = estTotal
    
    this._processTimer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this._processStartTime) / 1000)
      const remaining = Math.max(0, this._estTotal - elapsed)
      let stage = '上传中'
      if (this.data.uploadProgress >= 100) {
        stage = '识别中'
      }
      this.setData({ processingText: `${stage}，预计还需 ${remaining}秒` })
    }, 1000)
    
    const uploadTask = wx.uploadFile({
      url: app.globalData.baseUrl + '/transcribe',
      filePath: this.data.tempFilePath,
      name: 'file',
      formData: { language: this.data.language },
      timeout: 600000,
      success: (res) => {
        clearInterval(this._processTimer)
        const data = JSON.parse(res.data)
        this.setData({ resultText: data.text, uploading: false, uploadProgress: 0, processingText: '' })
        wx.setClipboardData({ data: data.text })
      },
      fail: (err) => {
        clearInterval(this._processTimer)
        console.error('Upload error:', err)
        wx.showToast({ title: '识别失败', icon: 'error' })
        this.setData({ uploading: false, uploadProgress: 0, processingText: '' })
      }
    })
    uploadTask.onProgressUpdate((res) => {
      this.setData({ uploadProgress: res.progress })
    })
  },

  trimSilence() {
    if (!this.data.tempFilePath) {
      wx.showToast({ title: '请先录音', icon: 'none' })
      return
    }
    this.setData({ trimming: true, trimResult: null })
    wx.uploadFile({
      url: app.globalData.baseUrl + '/trim-silence',
      filePath: this.data.tempFilePath,
      name: 'file',
      formData: { silence_threshold: '-40', min_silence_duration: '5' },
      success: (res) => {
        const data = JSON.parse(res.data)
        if (data.error) {
          wx.showToast({ title: data.error, icon: 'error' })
        } else {
          this.setData({
            tempFilePath: app.globalData.baseUrl + data.audio,
            trimResult: data,
            audioDuration: 0,
            audioCurrentTime: 0,
            sliderValue: 0,
            currentTime: '00:00'
          })
          wx.showToast({ title: `节省 ${data.saved_seconds}秒`, icon: 'success' })
        }
        this.setData({ trimming: false })
      },
      fail: () => {
        wx.showToast({ title: '裁剪失败', icon: 'error' })
        this.setData({ trimming: false })
      }
    })
  },

  transcribeTrimmed() {
    if (!this.data.tempFilePath) return
    this.transcribe()
  },

  saveTrimmedAudio() {
    if (!this.data.tempFilePath || !this.data.trimResult) return
    const fs = wx.getFileSystemManager()
    const filePath = `${wx.env.USER_DATA_PATH}/trimmed_${Date.now()}.mp3`
    wx.downloadFile({
      url: this.data.tempFilePath,
      success: (res) => {
        fs.writeFile({
          filePath: filePath,
          data: res.tempFilePath,
          encoding: 'binary',
          success: () => {
            wx.saveVideoToPhotosAlbum({
              filePath: filePath,
              success: () => {
                wx.showToast({ title: '已保存到相册', icon: 'success' })
              },
              fail: () => {
                wx.showToast({ title: '保存失败', icon: 'error' })
              }
            })
          }
        })
      }
    })
  },

  copyText() {
    if (!this.data.resultText) return
    wx.setClipboardData({
      data: this.data.resultText,
      success: () => wx.showToast({ title: '已复制全部', icon: 'success' })
    })
  },

  saveToHistoryBtn() {
    if (!this.data.resultText) return
    this.saveToHistory(this.data.resultText)
    wx.showToast({ title: '已保存', icon: 'success' })
  },

  copySelected() {
    if (!this.data.selectedText) {
      wx.showToast({ title: '请先选择文字', icon: 'none' })
      return
    }
    wx.setClipboardData({
      data: this.data.selectedText,
      success: () => wx.showToast({ title: '已复制选中', icon: 'success' })
    })
  },

  onTextSelect(e) {
    this.setData({ selectedText: e.detail.value })
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
    this._audio.onCanplay(() => {
      if (this._audio) {
        this.setData({ audioDuration: this._audio.duration })
      }
    })
    this._audio.onTimeUpdate(() => {
      if (this._audio && !this._isSliding) {
        const current = this._audio.currentTime
        const duration = this._audio.duration || 1
        this.setData({
          currentTime: this.formatTime(Math.floor(current)),
          audioCurrentTime: current,
          sliderValue: (current / duration) * 100
        })
      }
    })
    this._audio.onEnded(() => {
      this.setData({ isPlaying: false, currentTime: '00:00', sliderValue: 0, audioCurrentTime: 0 })
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

  onSliderChanging(e) {
    this._isSliding = true
    const duration = this._audio ? this._audio.duration : 1
    const currentTime = (e.detail.value / 100) * duration
    this.setData({ audioCurrentTime: currentTime, currentTime: this.formatTime(Math.floor(currentTime)) })
  },

  onSliderChange(e) {
    this._isSliding = false
    if (this._audio) {
      const duration = this._audio.duration || 1
      const seekTime = (e.detail.value / 100) * duration
      this._audio.seek(seekTime)
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
    clearInterval(this._processTimer)
    this.setData({
      tempFilePath: '', resultText: '', isPlaying: false, playbackRate: 1,
      currentTime: '00:00', audioDuration: 0, audioCurrentTime: 0, sliderValue: 0,
      selectedText: '', uploading: false, uploadProgress: 0, processingText: '',
      isVideo: false, fileName: ''
    })
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
      duration: this.data.durationText,
      title: this.data.fileName || '录音'
    }
    history.unshift(item)
    if (history.length > 100) {
      history = history.slice(0, 100)
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
