import { ref } from "vue"

export function useGeolocation() {
  const position = ref(null)
  const error = ref(null)
  const isSupported = "geolocation" in navigator

  const getCurrentPosition = () => {
    if (!isSupported) {
      error.value = new Error("Geolocation is not supported by this browser")
      return Promise.reject(error.value)
    }

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          position.value = pos
          resolve(pos)
        },
        (err) => {
          error.value = err
          reject(err)
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        },
      )
    })
  }

  const watchPosition = () => {
    if (!isSupported) {
      error.value = new Error("Geolocation is not supported by this browser")
      return null
    }

    return navigator.geolocation.watchPosition(
      (pos) => {
        position.value = pos
      },
      (err) => {
        error.value = err
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    )
  }

  return {
    position,
    error,
    isSupported,
    getCurrentPosition,
    watchPosition,
  }
}

