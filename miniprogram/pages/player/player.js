const app = getApp()
const innerAudioContext = wx.createInnerAudioContext()

Page({
  data: {
    note: null,
    currentSegment: 0,
    isPlaying: false,
    currentTime: '00:00',
    duration: '00:00'
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
      this.setData({ isPlaying: false })
      if (this.data.currentSegment < this.data.note.segments.length - 1) {
        this.setData({ currentSegment: this.data.currentSegment + 1 })
        this.initAudio()
      }
    })
  },

  togglePlay() {
    if (this.data.isPlaying) {
      innerAudioContext.pause()
    } else {
      innerAudioContext.play()
    }
    this.setData({ isPlaying: !this.data.isPlaying })
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
