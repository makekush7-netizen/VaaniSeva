import React, { useEffect, useRef } from 'react'
import { useGLTF } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

/**
 * AvatarModel — Renders a 3D GLB avatar with:
 *   - Idle + bashful animation loop
 *   - Eye bone tracking (follows camera)
 *   - Blinking (morph targets or mesh scale fallback)
 *   - Emotional morphs (happy, laugh, shock, sad)
 *   - Lip sync via aura:setMorph events (mouthOpen)
 *   - Animation control via aura:setAnimation events
 *
 * Copied from AuraMart and is model-agnostic — works with any
 * Ready Player Me / Mixamo .glb that has standard morph targets.
 */
export default function AvatarModel({
  modelUrl = '/models/model_female.glb',
  scale = 1,
  position = [0, 0, 0],
  mini = false,
  showWaistUp = false
}) {
  const gltf = useGLTF(modelUrl)
  const { scene, animations } = gltf
  const mixerRef = useRef(null)
  const eyeBonesRef = useRef({ left: [], right: [] })
  const idleTimeRef = useRef(0)
  const blinkTimerRef = useRef(0)
  const actionsRef = useRef({})

  const adjustedPosition = showWaistUp
    ? [position[0], position[1], position[2]]
    : position

  // ── Setup animation mixer ───────────────────────────
  useEffect(() => {
    if (animations && animations.length > 0) {
      const mixer = new THREE.AnimationMixer(scene)
      mixerRef.current = mixer

      animations.forEach((clip) => {
        const action = mixer.clipAction(clip)
        actionsRef.current[clip.name.toLowerCase()] = action
      })

      // Auto-play idle
      const idleAction =
        actionsRef.current['mainidle'] ||
        actionsRef.current['idle'] ||
        Object.values(actionsRef.current)[0]
      if (idleAction) idleAction.play()

      // Random bashful loop
      if (actionsRef.current['bashful']) {
        setInterval(() => {
          const bash = actionsRef.current['bashful']
          const main = actionsRef.current['mainidle'] || idleAction
          if (Math.random() > 0.6) {
            bash.reset().fadeIn(0.5).play()
            main.fadeOut(0.5)
            setTimeout(() => {
              main.reset().fadeIn(0.5).play()
              bash.fadeOut(0.5)
            }, 4000)
          }
        }, 8000)
      }
    }
  }, [animations, scene])

  // ── Find eye bones ──────────────────────────────────
  useEffect(() => {
    scene.traverse((node) => {
      if (node.isBone) {
        const n = node.name.toLowerCase()
        if (n.includes('lefteye') || n === 'eyeleft' || n === 'eye_l' || n.includes('eye.l')) {
          eyeBonesRef.current.left.push(node)
        }
        if (n.includes('righteye') || n === 'eyeright' || n === 'eye_r' || n.includes('eye.r')) {
          eyeBonesRef.current.right.push(node)
        }
      }
    })
  }, [scene])

  // ── Animation control events ────────────────────────
  useEffect(() => {
    let currentIdle =
      actionsRef.current['mainidle'] ||
      actionsRef.current['idle'] ||
      Object.values(actionsRef.current)[0]

    const playAction = (name, isOneShot = true) => {
      const action =
        actionsRef.current[name] ||
        actionsRef.current[Object.keys(actionsRef.current).find((k) => k.includes(name))]

      if (action && action !== currentIdle) {
        action.reset()
        action.setLoop(isOneShot ? THREE.LoopOnce : THREE.LoopRepeat)
        action.clampWhenFinished = isOneShot
        action.fadeIn(0.5).play()
        if (currentIdle) currentIdle.fadeOut(0.5)

        if (isOneShot) {
          const duration = action.getClip().duration * 1000
          setTimeout(() => {
            action.fadeOut(0.5)
            if (currentIdle) currentIdle.reset().fadeIn(0.5).play()
          }, duration - 500)
        }
      }
    }

    const onTalking = (e) => {
      const isTalking = e.detail
      const talkAction = actionsRef.current['talk'] || actionsRef.current['talking']
      if (isTalking && talkAction) {
        talkAction.reset().fadeIn(0.5).play()
      } else if (talkAction) {
        talkAction.fadeOut(0.5)
      }
    }

    const onEmotion = (e) => {
      const emo = e.detail
      if (emo === 'happy') playAction('waveing', true) || playAction('wave', true)
      if (emo === 'laugh') playAction('laughing', true) || playAction('laugh', true)
      if (emo === 'shock') playAction('surprised', true) || playAction('shock', true)
      if (emo === 'sad') playAction('bashful', false) || playAction('sad', false)
      if (emo === 'thankful') playAction('thankful', true)
      if (emo === 'thinking') playAction('thinking', false)
    }

    const onSetAnimation = (e) => {
      const animName = e.detail?.toLowerCase()
      if (animName && actionsRef.current[animName]) {
        Object.values(actionsRef.current).forEach((a) => a.fadeOut(0.3))
        actionsRef.current[animName].reset().fadeIn(0.3).play()
      }
    }

    window.addEventListener('aura:talking', onTalking)
    window.addEventListener('aura:setEmotion', onEmotion)
    window.addEventListener('aura:setAnimation', onSetAnimation)
    return () => {
      window.removeEventListener('aura:talking', onTalking)
      window.removeEventListener('aura:setEmotion', onEmotion)
      window.removeEventListener('aura:setAnimation', onSetAnimation)
    }
  }, [animations])

  // ── Lip-sync morph control ──────────────────────────
  useEffect(() => {
    function onSetMorph(e) {
      const { name, value } = e?.detail || {}
      if (!name || typeof value !== 'number') return
      scene.traverse((node) => {
        if (!node.isMesh) return
        const dict = node.morphTargetDictionary
        const inf = node.morphTargetInfluences
        if (dict && inf) {
          const idx = dict[name]
          if (typeof idx === 'number') inf[idx] = value
        }
      })
    }
    window.addEventListener('aura:setMorph', onSetMorph)
    return () => window.removeEventListener('aura:setMorph', onSetMorph)
  }, [scene])

  // ── Eye direction control ───────────────────────────
  useEffect(() => {
    function onSetEye(e) {
      let { yaw = 0, pitch = 0 } = e?.detail || {}
      pitch = Math.max(-0.14, Math.min(0.14, pitch))
      const applyToBones = (list, y, p) => {
        list.forEach((b) => {
          try { b.rotation.y = y; b.rotation.x = p } catch (_) {}
        })
      }
      applyToBones(eyeBonesRef.current.left, yaw, pitch)
      applyToBones(eyeBonesRef.current.right, yaw, pitch)
    }
    window.addEventListener('aura:setEye', onSetEye)
    return () => window.removeEventListener('aura:setEye', onSetEye)
  }, [scene])

  // ── Emotion state ───────────────────────────────────
  const emotionRef = useRef('neutral')
  useEffect(() => {
    const onEmotion = (e) => {
      emotionRef.current = e.detail || 'neutral'
      setTimeout(() => { emotionRef.current = 'neutral' }, 3000)
    }
    window.addEventListener('aura:setEmotion', onEmotion)
    return () => window.removeEventListener('aura:setEmotion', onEmotion)
  }, [])

  // ── Per-frame loop ──────────────────────────────────
  useFrame((state, delta) => {
    if (mixerRef.current) mixerRef.current.update(delta)
    idleTimeRef.current += delta
    blinkTimerRef.current += delta

    // Breathing
    const breathe = 1 + Math.sin(idleTimeRef.current * 1.5) * 0.008
    scene.scale.setScalar(scale * breathe)

    // Blinking
    if (blinkTimerRef.current > 4 + Math.random() * 4) {
      blinkTimerRef.current = 0
      let blinked = false
      scene.traverse((node) => {
        if (node.isMesh && node.morphTargetDictionary) {
          const dict = node.morphTargetDictionary
          const leftIdx = dict['eyesClosed'] || dict['eyeBlinkLeft'] || dict['eyeBlink_L'] || dict['Blink'] || dict['blink']
          const rightIdx = dict['eyeBlinkRight'] || dict['eyeBlink_R']
          if (leftIdx !== undefined) {
            try { node.morphTargetInfluences[leftIdx] = 1; setTimeout(() => node.morphTargetInfluences[leftIdx] = 0, 150); blinked = true } catch (_) {}
          }
          if (rightIdx !== undefined && rightIdx !== leftIdx) {
            try { node.morphTargetInfluences[rightIdx] = 1; setTimeout(() => node.morphTargetInfluences[rightIdx] = 0, 150); blinked = true } catch (_) {}
          }
        }
      })
      if (!blinked) {
        scene.traverse((node) => {
          if (node.isMesh && (node.name.includes('Eye') || node.name.includes('eye'))) {
            const origY = node.userData.origScaleY || node.scale.y
            node.userData.origScaleY = origY
            node.scale.y = 0.1
            setTimeout(() => { node.scale.y = origY }, 150)
          }
        })
      }
    }

    // Eye tracking + saccades
    if (!mini) {
      const camPos = state.camera.position
      const time = state.clock.elapsedTime
      const saccadeX = Math.sin(time * 0.5) * 0.05 + (Math.random() > 0.98 ? (Math.random() - 0.5) * 0.2 : 0)
      const saccadeY = Math.cos(time * 0.3) * 0.05 + (Math.random() > 0.98 ? (Math.random() - 0.5) * 0.1 : 0)

      const trackEye = (bones) => {
        bones.forEach((bone) => {
          const dx = camPos.x, dy = camPos.y - 1.55, dz = camPos.z
          const targetYaw = Math.atan2(dx, dz) + saccadeX
          const targetPitch = Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)) + saccadeY
          const yaw = Math.max(-0.6, Math.min(0.6, targetYaw))
          const pitch = Math.max(-0.35, Math.min(0.35, -targetPitch))
          bone.rotation.y = THREE.MathUtils.lerp(bone.rotation.y, yaw, 0.2)
          bone.rotation.x = THREE.MathUtils.lerp(bone.rotation.x, pitch, 0.2)
        })
      }
      trackEye(eyeBonesRef.current.left)
      trackEye(eyeBonesRef.current.right)
    }

    // Emotional morphs
    scene.traverse((node) => {
      if (node.isMesh && node.morphTargetDictionary && node.morphTargetInfluences) {
        const dict = node.morphTargetDictionary
        const infl = node.morphTargetInfluences
        const resetMorph = (key) => {
          if (key !== 'eyesClosed' && dict[key] !== undefined)
            infl[dict[key]] = THREE.MathUtils.lerp(infl[dict[key]], 0, 0.1)
        }
        ;['mouthSmile', 'browInnerUp', 'jawOpen', 'mouthOpen', 'browOuterUp', 'eyeWide', 'mouthFrown', 'browDown'].forEach(resetMorph)

        if (emotionRef.current === 'happy') {
          if (dict['mouthSmile'] !== undefined) infl[dict['mouthSmile']] = THREE.MathUtils.lerp(infl[dict['mouthSmile']], 1.0, 0.2)
          if (dict['browInnerUp'] !== undefined) infl[dict['browInnerUp']] = THREE.MathUtils.lerp(infl[dict['browInnerUp']], 1.0, 0.2)
          if (dict['eyeSquintLeft'] !== undefined) infl[dict['eyeSquintLeft']] = THREE.MathUtils.lerp(infl[dict['eyeSquintLeft']], 0.6, 0.2)
          if (dict['eyeSquintRight'] !== undefined) infl[dict['eyeSquintRight']] = THREE.MathUtils.lerp(infl[dict['eyeSquintRight']], 0.6, 0.2)
        } else if (emotionRef.current === 'laugh') {
          if (dict['eyesClosed'] !== undefined) infl[dict['eyesClosed']] = THREE.MathUtils.lerp(infl[dict['eyesClosed']], 1, 0.2)
          if (dict['mouthSmile'] !== undefined) infl[dict['mouthSmile']] = 1
          const laughVal = 0.2 + Math.abs(Math.sin(state.clock.elapsedTime * 15)) * 0.5
          const openMorph = dict['mouthOpen'] !== undefined ? 'mouthOpen' : 'jawOpen'
          if (dict[openMorph] !== undefined) infl[dict[openMorph]] = THREE.MathUtils.lerp(infl[dict[openMorph]], laughVal, 0.2)
        } else if (emotionRef.current === 'shock') {
          const openMorph = dict['mouthOpen'] !== undefined ? 'mouthOpen' : 'jawOpen'
          if (dict[openMorph] !== undefined) infl[dict[openMorph]] = THREE.MathUtils.lerp(infl[dict[openMorph]], 0.6, 0.2)
          const browMorph = dict['browOuterUp'] !== undefined ? 'browOuterUp' : 'browInnerUp'
          if (dict[browMorph] !== undefined) infl[dict[browMorph]] = THREE.MathUtils.lerp(infl[dict[browMorph]], 1, 0.2)
          if (dict['eyeWide'] !== undefined) infl[dict['eyeWide']] = THREE.MathUtils.lerp(infl[dict['eyeWide']], 1, 0.2)
        } else if (emotionRef.current === 'sad') {
          const frown = dict['mouthFrown'] !== undefined ? 'mouthFrown' :
            dict['mouthRollLower'] !== undefined ? 'mouthRollLower' :
            dict['mouthShrugLower'] !== undefined ? 'mouthShrugLower' : 'mouthPucker'
          if (dict[frown] !== undefined) infl[dict[frown]] = THREE.MathUtils.lerp(infl[dict[frown]], 0.8, 0.1)
          if (dict['browDown'] !== undefined) infl[dict['browDown']] = THREE.MathUtils.lerp(infl[dict['browDown']], 0.8, 0.1)
        }
      }
    })
  })

  return <primitive object={scene} scale={scale} position={adjustedPosition} />
}

useGLTF.preload('/models/model_female.glb')
