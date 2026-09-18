App({
  globalData: {
    baseUrl: (() => {
      const saved = wx.getStorageSync('serverUrl')
      // 迁移本机旧 IP，保留用户配置的其他服务器地址。
      if (!saved || /^http:\/\/10\.0\.5\.165:8000\/?$/.test(saved)) {
        return 'http://10.0.5.202:8000'
      }
      return saved
    })()
  },
  setServerUrl(url) {
    this.globalData.baseUrl = url
    wx.setStorageSync('serverUrl', url)
  }
})
