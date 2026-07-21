const app = getApp()
const innerAudioContext = wx.createInnerAudioContext()

Page({
  data: {
    note: null,
    currentSegment: 0,
    isPlaying: false,
    currentTime: '00:00',
    duration: '00:00',
    autoPlay: true,
    sleepTimer: false
  },

  onLoad(options) {
    const notes = wx.getStorageSync('notes') || []
    const note = notes.find(n => n.id === options.id)
    if (note) {
      this.setData({ note })
      this.initAudio()
    }
  },

  initAudio() {
    const { note, currentSegment } = this.data
    if (!note || !note.segments[currentSegment]) return

    const segment = note.segments[currentSegment]
    innerAudioContext.src = app.globalData.baseUrl + segment.audio

    innerAudioContext.onTimeUpdate(() => {
      const currentTime = this.formatTime(innerAudioContext.currentTime)
      const duration = this.formatTime(innerAudioContext.duration)
      this.setData({ currentTime, duration })
    })

    innerAudioContext.onEnded(() => {
      if (this.data.sleepTimer) {
        this.setData({ isPlaying: false })
        return
      }
      if (this.data.currentSegment < this.data.note.segments.length - 1) {
        this.setData({ currentSegment: this.data.currentSegment + 1 })
        this.initAudio()
        if (this.data.isPlaying || this.data.autoPlay) {
          innerAudioContext.play()
          this.setData({ isPlaying: true })
        }
      } else {
        this.setData({ isPlaying: false, currentSegment: 0 })
        this.initAudio()
      }
    })

    innerAudioContext.onError((err) => {
      console.error('Audio error:', err)
      this.setData({ isPlaying: false })
    })
  },

  togglePlay() {
    if (this.data.isPlaying) {
      innerAudioContext.pause()
      this.setData({ isPlaying: false })
    } else {
      innerAudioContext.play()
      this.setData({ isPlaying: true })
    }
  },

  toggleAutoPlay() {
    this.setData({ autoPlay: !this.data.autoPlay })
    wx.showToast({ title: this.data.autoPlay ? '已开启连播' : '已关闭连播', icon: 'none' })
  },

  toggleSleep() {
    this.setData({ sleepTimer: !this.data.sleepTimer })
    wx.showToast({ title: this.data.sleepTimer ? '播完当前段停止' : '已关闭', icon: 'none' })
  },

  prevSegment() {
    if (this.data.currentSegment > 0) {
      this.setData({ currentSegment: this.data.currentSegment - 1 })
      this.initAudio()
      if (this.data.isPlaying) innerAudioContext.play()
    }
  },

  nextSegment() {
    if (this.data.currentSegment < this.data.note.segments.length - 1) {
      this.setData({ currentSegment: this.data.currentSegment + 1 })
      this.initAudio()
      if (this.data.isPlaying) innerAudioContext.play()
    }
  },

  formatTime(seconds) {
    const min = Math.floor(seconds / 60)
    const sec = Math.floor(seconds % 60)
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  },

  onUnload() {
    innerAudioContext.stop()
  }
})
