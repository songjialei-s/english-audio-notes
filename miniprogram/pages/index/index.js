const app = getApp()

Page({
  data: {
    notes: [],
    uploading: false,
    uploadTask: null,
    voices: [],
    voiceIndex: 0,
    currentVoice: '默认',
    rates: [100, 120, 150, 180, 200],
    rateIndex: 2,
    currentRate: 150
  },

  onLoad() {
    this.loadNotes()
    this.loadVoices()
  },

  loadVoices() {
    wx.request({
      url: app.globalData.baseUrl + '/voices',
      success: (res) => {
        const list = res.data.map(v => ({
          id: v.id,
          name: v.name,
          lang: v.lang,
          label: `${v.lang === 'zh' ? '中文' : '英文'} - ${v.name.split(' - ').pop()}`
        }))
        this.setData({ voices: list })
      }
    })
  },

  changeVoice(e) {
    const idx = e.detail.value
    const voice = this.data.voices[idx]
    this.setData({ voiceIndex: idx, currentVoice: voice.label })
  },

  changeRate(e) {
    const idx = e.detail.value
    const rate = this.data.rates[idx]
    this.setData({ rateIndex: idx, currentRate: rate })
  },

  loadNotes() {
    const notes = wx.getStorageSync('notes') || []
    this.setData({ notes })
  },

  uploadPDF() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['pdf'],
      success: (res) => {
        const file = res.tempFiles[0]
        this.setData({ uploading: true })

        const voiceId = this.data.voices[this.data.voiceIndex] ? this.data.voices[this.data.voiceIndex].id : ''
        const rate = this.data.currentRate

        const task = wx.uploadFile({
          url: app.globalData.baseUrl + '/upload',
          filePath: file.path,
          name: 'file',
          formData: { voice_id: voiceId, rate: rate },
          timeout: 600000,
          success: (uploadRes) => {
            this.setData({ uploading: false })
            const data = JSON.parse(uploadRes.data)
            const note = {
              id: data.id,
              name: file.name,
              segments: data.segments,
              createdAt: Date.now()
            }

            const notes = wx.getStorageSync('notes') || []
            notes.unshift(note)
            wx.setStorageSync('notes', notes)
            this.loadNotes()

            wx.navigateTo({
              url: `/pages/player/player?id=${data.id}`
            })
          },
          fail: () => {
            this.setData({ uploading: false })
            wx.showToast({ title: '上传失败', icon: 'error' })
          }
        })

        this.setData({ uploadTask: task })
      }
    })
  },

  cancelUpload() {
    const task = this.data.uploadTask
    if (task) {
      task.abort()
      this.setData({ uploading: false, uploadTask: null })
      wx.showToast({ title: '已取消', icon: 'none' })
    }
  },

  playNote(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/player/player?id=${id}`
    })
  },

  deleteNote(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个笔记吗？',
      success: (res) => {
        if (res.confirm) {
          let notes = wx.getStorageSync('notes') || []
          notes = notes.filter(n => n.id !== id)
          wx.setStorageSync('notes', notes)
          this.loadNotes()
        }
      }
    })
  }
})
