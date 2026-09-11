import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export const ThreeStoryScene = ({ scrollProgress = 0, activeChapter = 1 }) => {
  const mountRef = useRef(null);
  const sceneStateRef = useRef({
    scene: null,
    camera: null,
    renderer: null,
    islandGroup: null,
    crops: [],
    particles: null,
    sunMesh: null,
    alertBeacon: null,
    voiceOrbGroup: null,
    shieldGroup: null,
    harvestGroup: null,
    currentCamPos: new THREE.Vector3(0, 11, 25),
    currentLookAt: new THREE.Vector3(0, 1, 0),
    targetCamPos: new THREE.Vector3(0, 11, 25),
    targetLookAt: new THREE.Vector3(0, 1, 0),
    mouse: { x: 0, y: 0, targetX: 0, targetY: 0 },
    reqId: null,
  });

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene & Deep Organic Evergreen Fog (#08110A)
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x08110a, 0.022);

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
    camera.position.set(0, 11, 25);

    // 3. High Dynamic Range Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. Studio Lighting (Zenze Warm Sunlight & Vibrant Lime Speculars)
    const ambientLight = new THREE.AmbientLight(0x0f2415, 1.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xfffaea, 2.5);
    dirLight.position.set(22, 34, 18);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.bias = -0.0001;
    scene.add(dirLight);

    // Zenze Lime-Pistachio Accent Light (#A3E635)
    const limeGlowLight = new THREE.PointLight(0xa3e635, 4.2, 45);
    limeGlowLight.position.set(0, 6, 2);
    scene.add(limeGlowLight);

    const warmMorningLight = new THREE.PointLight(0xfacc15, 2.2, 35);
    warmMorningLight.position.set(-14, 9, -12);
    scene.add(warmMorningLight);

    // 5. 3D Floating Terrace Plantation Island
    const islandGroup = new THREE.Group();

    // Deep Forest Monolith Base
    const baseGeo = new THREE.CylinderGeometry(15.5, 17.5, 2.5, 64);
    const baseMat = new THREE.MeshStandardMaterial({
      color: 0x08160d,
      roughness: 0.6,
      metalness: 0.25,
      flatShading: true,
    });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = -1.25;
    baseMesh.receiveShadow = true;
    islandGroup.add(baseMesh);

    // Top Rich Soil Layer
    const topPlateGeo = new THREE.CylinderGeometry(15.2, 15.2, 0.28, 64);
    const topPlateMat = new THREE.MeshStandardMaterial({
      color: 0x112618,
      roughness: 0.85,
    });
    const topPlateMesh = new THREE.Mesh(topPlateGeo, topPlateMat);
    topPlateMesh.position.y = 0.06;
    topPlateMesh.receiveShadow = true;
    islandGroup.add(topPlateMesh);

    // Zenze Lime Hairline Grid Matrix
    const gridGeo = new THREE.RingGeometry(0.8, 15.0, 64, 10);
    const gridMat = new THREE.MeshBasicMaterial({
      color: 0xa3e635,
      wireframe: true,
      transparent: true,
      opacity: 0.18,
    });
    const gridMesh = new THREE.Mesh(gridGeo, gridMat);
    gridMesh.rotation.x = -Math.PI / 2;
    gridMesh.position.y = 0.22;
    islandGroup.add(gridMesh);

    // 6. 3D Plantation Stalks with Wind Dynamics
    const crops = [];
    const numRows = 8;
    const numCols = 8;

    for (let i = -numRows / 2; i <= numRows / 2; i++) {
      for (let j = -numCols / 2; j <= numCols / 2; j++) {
        const x = i * 2.6 + (Math.random() - 0.5) * 0.4;
        const z = j * 2.6 + (Math.random() - 0.5) * 0.4;
        const dist = Math.sqrt(x * x + z * z);

        if (dist < 13.5 && dist > 1.4) {
          const stemH = 1.4 + Math.random() * 0.8;
          const stemGeo = new THREE.CylinderGeometry(0.04, 0.09, stemH, 6);
          const stemMat = new THREE.MeshStandardMaterial({
            color: 0x65a30d,
            roughness: 0.4,
            emissive: 0x142c19,
            emissiveIntensity: 0.25,
          });
          const stem = new THREE.Mesh(stemGeo, stemMat);
          stem.position.set(x, stemH / 2 + 0.22, z);
          stem.castShadow = true;

          // Foliage Head Cluster in Pistachio
          const headGeo = new THREE.DodecahedronGeometry(0.28, 0);
          const headMat = new THREE.MeshStandardMaterial({
            color: 0xd9f99d,
            emissive: 0xa3e635,
            emissiveIntensity: 0.35,
            roughness: 0.25,
          });
          const head = new THREE.Mesh(headGeo, headMat);
          head.position.y = stemH / 2;
          stem.add(head);

          islandGroup.add(stem);
          crops.push({
            mesh: stem,
            headMesh: head,
            baseX: x,
            baseZ: z,
            phase: Math.random() * Math.PI * 2,
            speed: 1.4 + Math.random() * 1.6,
          });
        }
      }
    }
    scene.add(islandGroup);

    // 7. Ambient Glowing Pistachio & Dew Mist Particles
    const pCount = 300;
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(pCount * 3);
    const pCols = new Float32Array(pCount * 3);

    for (let k = 0; k < pCount; k++) {
      pPos[k * 3] = (Math.random() - 0.5) * 48;
      pPos[k * 3 + 1] = Math.random() * 22;
      pPos[k * 3 + 2] = (Math.random() - 0.5) * 48;

      const isLime = k % 2 === 0;
      const c = new THREE.Color(isLime ? 0xa3e635 : 0xfef08a);
      pCols[k * 3] = c.r;
      pCols[k * 3 + 1] = c.g;
      pCols[k * 3 + 2] = c.b;
    }

    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    pGeo.setAttribute('color', new THREE.BufferAttribute(pCols, 3));

    const pMat = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    // 8. 3D Chapter 1 Object: Golden Dawn Sun & Crop Symptom Beacon
    const sunGeo = new THREE.SphereGeometry(3.5, 32, 32);
    const sunMat = new THREE.MeshBasicMaterial({ color: 0xfacc15 });
    const sunMesh = new THREE.Mesh(sunGeo, sunMat);
    sunMesh.position.set(-15, 11, -16);
    scene.add(sunMesh);

    // Distress Beacon
    const alertBeacon = new THREE.Group();
    const bRingGeo = new THREE.RingGeometry(0.3, 0.7, 32);
    const bRingMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.9,
    });
    const bRing = new THREE.Mesh(bRingGeo, bRingMat);
    bRing.rotation.x = Math.PI / 2;
    alertBeacon.add(bRing);

    const bPillarGeo = new THREE.CylinderGeometry(0.02, 0.02, 5, 8);
    const bPillarMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      transparent: true,
      opacity: 0.6,
    });
    const bPillar = new THREE.Mesh(bPillarGeo, bPillarMat);
    bPillar.position.y = 2.5;
    alertBeacon.add(bPillar);

    alertBeacon.position.set(4.2, 0.5, 3.8);
    scene.add(alertBeacon);

    // 9. 3D Chapter 2 Object: Holographic Lime AI Voice Wave Resonator
    const voiceOrbGroup = new THREE.Group();
    for (let v = 0; v < 5; v++) {
      const vTorusGeo = new THREE.TorusGeometry(1.5 + v * 0.8, 0.045, 16, 64);
      const vTorusMat = new THREE.MeshStandardMaterial({
        color: v % 2 === 0 ? 0xa3e635 : 0x38bdf8,
        emissive: v % 2 === 0 ? 0xa3e635 : 0x0284c7,
        emissiveIntensity: 1.4,
        transparent: true,
        opacity: 0.95 - v * 0.12,
      });
      const vTorus = new THREE.Mesh(vTorusGeo, vTorusMat);
      vTorus.rotation.x = Math.PI / 2;
      voiceOrbGroup.add(vTorus);
    }
    const voiceCoreGeo = new THREE.SphereGeometry(0.75, 32, 32);
    const voiceCoreMat = new THREE.MeshStandardMaterial({
      color: 0xa3e635,
      emissive: 0xa3e635,
      emissiveIntensity: 1.6,
      roughness: 0.1,
    });
    const voiceCore = new THREE.Mesh(voiceCoreGeo, voiceCoreMat);
    voiceOrbGroup.add(voiceCore);
    voiceOrbGroup.position.set(0, 4.2, 0);
    scene.add(voiceOrbGroup);

    // 10. 3D Chapter 3 Object: Crystalline Knowledge Shield & 1,500+ Nodes
    const shieldGroup = new THREE.Group();
    const shieldCoreGeo = new THREE.IcosahedronGeometry(2.5, 1);
    const shieldCoreMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      wireframe: true,
      emissive: 0xa3e635,
      emissiveIntensity: 1.2,
    });
    const shieldCore = new THREE.Mesh(shieldCoreGeo, shieldCoreMat);
    shieldGroup.add(shieldCore);

    for (let s = 0; s < 7; s++) {
      const satGeo = new THREE.OctahedronGeometry(0.32, 0);
      const satMat = new THREE.MeshStandardMaterial({
        color: 0xa3e635,
        emissive: 0x65a30d,
        emissiveIntensity: 1.1,
      });
      const sat = new THREE.Mesh(satGeo, satMat);
      const ang = (s * Math.PI * 2) / 7;
      sat.position.set(Math.cos(ang) * 4.0, Math.sin(s * 1.6) * 1.3, Math.sin(ang) * 4.0);
      shieldGroup.add(sat);
    }
    shieldGroup.position.set(0, 4.4, 0);
    scene.add(shieldGroup);

    // 11. 3D Chapter 4 Object: Golden Harvest Prosperity Bloom
    const harvestGroup = new THREE.Group();
    const hBloomGeo = new THREE.DodecahedronGeometry(2.4, 1);
    const hBloomMat = new THREE.MeshStandardMaterial({
      color: 0xa3e635,
      emissive: 0x84cc16,
      emissiveIntensity: 1.3,
      metalness: 0.8,
      roughness: 0.2,
    });
    const hBloom = new THREE.Mesh(hBloomGeo, hBloomMat);
    harvestGroup.add(hBloom);

    for (let r = 0; r < 8; r++) {
      const ribGeo = new THREE.CylinderGeometry(0.04, 0.09, 4.0, 6);
      const ribMat = new THREE.MeshStandardMaterial({
        color: 0xfacc15,
        emissive: 0xeab308,
        emissiveIntensity: 1.1,
      });
      const rib = new THREE.Mesh(ribGeo, ribMat);
      const ang = (r * Math.PI * 2) / 8;
      rib.position.set(Math.cos(ang) * 2.8, 1.4, Math.sin(ang) * 2.8);
      rib.rotation.z = 0.28 * Math.sin(ang);
      harvestGroup.add(rib);
    }
    harvestGroup.position.set(0, 4.2, 0);
    scene.add(harvestGroup);

    // Save refs
    sceneStateRef.current = {
      scene,
      camera,
      renderer,
      islandGroup,
      crops,
      particles,
      sunMesh,
      alertBeacon,
      voiceOrbGroup,
      shieldGroup,
      harvestGroup,
      currentCamPos: new THREE.Vector3(0, 11, 25),
      currentLookAt: new THREE.Vector3(0, 1, 0),
      targetCamPos: new THREE.Vector3(0, 11, 25),
      targetLookAt: new THREE.Vector3(0, 1, 0),
      mouse: { x: 0, y: 0, targetX: 0, targetY: 0 },
      reqId: null,
    };

    // Mouse Tracking for Parallax
    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      sceneStateRef.current.mouse.targetX = x * 3.0;
      sceneStateRef.current.mouse.targetY = y * 2.0;
    };

    const handleResize = () => {
      if (!mountRef.current || !renderer || !camera) return;
      const w = mountRef.current.clientWidth || window.innerWidth;
      const h = mountRef.current.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);

    // Animation Loop
    let clock = new THREE.Clock();

    const animate = () => {
      const elapsed = clock.getElapsedTime();

      // Mouse lerp
      const m = sceneStateRef.current.mouse;
      m.x += (m.targetX - m.x) * 0.06;
      m.y += (m.targetY - m.y) * 0.06;

      // Crop Procedural Wind Sway
      crops.forEach((c) => {
        c.mesh.rotation.z = Math.sin(elapsed * c.speed + c.phase) * 0.11;
        c.mesh.rotation.x = Math.cos(elapsed * c.speed * 0.75 + c.phase) * 0.08;
      });

      // Floating Particle Mist Movement
      if (particles) {
        particles.rotation.y = elapsed * 0.035;
        const pos = particles.geometry.attributes.position.array;
        for (let pIdx = 1; pIdx < pos.length; pIdx += 3) {
          pos[pIdx] += Math.sin(elapsed + pIdx) * 0.005;
        }
        particles.geometry.attributes.position.needsUpdate = true;
      }

      // Island Idle Rotation
      islandGroup.rotation.y = elapsed * 0.045;

      // Chapter Object Animations
      if (sunMesh) {
        sunMesh.position.y = 10 + Math.sin(elapsed * 0.7) * 0.7;
      }

      if (alertBeacon) {
        const pulse = 1 + Math.sin(elapsed * 4.5) * 0.35;
        alertBeacon.children[0].scale.set(pulse, pulse, 1);
      }

      if (voiceOrbGroup) {
        voiceOrbGroup.rotation.z = elapsed * 0.55;
        voiceOrbGroup.children.forEach((ring, idx) => {
          if (idx < 5) {
            const sc = 1 + Math.sin(elapsed * 3.8 + idx * 0.8) * 0.15;
            ring.scale.set(sc, sc, sc);
          }
        });
      }

      if (shieldGroup) {
        shieldGroup.rotation.y = elapsed * 0.75;
        shieldGroup.rotation.x = Math.sin(elapsed * 0.45) * 0.22;
      }

      if (harvestGroup) {
        harvestGroup.rotation.y = -elapsed * 0.65;
        const hPulse = 1 + Math.sin(elapsed * 2.4) * 0.09;
        harvestGroup.scale.set(hPulse, hPulse, hPulse);
      }

      // Continuous Smooth Camera Lerping along Scroll Trajectory
      const { targetCamPos, targetLookAt, currentCamPos, currentLookAt } = sceneStateRef.current;

      currentCamPos.x += (targetCamPos.x + m.x - currentCamPos.x) * 0.055;
      currentCamPos.y += (targetCamPos.y + m.y - currentCamPos.y) * 0.055;
      currentCamPos.z += (targetCamPos.z - currentCamPos.z) * 0.055;

      currentLookAt.x += (targetLookAt.x - currentLookAt.x) * 0.055;
      currentLookAt.y += (targetLookAt.y - currentLookAt.y) * 0.055;
      currentLookAt.z += (targetLookAt.z - currentLookAt.z) * 0.055;

      camera.position.copy(currentCamPos);
      camera.lookAt(currentLookAt);

      renderer.render(scene, camera);
      sceneStateRef.current.reqId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      if (sceneStateRef.current.reqId) cancelAnimationFrame(sceneStateRef.current.reqId);
      renderer.dispose();
      if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement);
    };
  }, []);

  // Update 3D Camera & Object Visibility based on Continuous Scroll Progress (0 to 1)
  useEffect(() => {
    const { sunMesh, alertBeacon, voiceOrbGroup, shieldGroup, harvestGroup, targetCamPos, targetLookAt } = sceneStateRef.current;
    if (!targetCamPos) return;

    if (sunMesh) sunMesh.visible = scrollProgress < 0.35;
    if (alertBeacon) alertBeacon.visible = scrollProgress < 0.35;
    if (voiceOrbGroup) voiceOrbGroup.visible = scrollProgress >= 0.20 && scrollProgress < 0.60;
    if (shieldGroup) shieldGroup.visible = scrollProgress >= 0.45 && scrollProgress < 0.85;
    if (harvestGroup) harvestGroup.visible = scrollProgress >= 0.70;

    if (scrollProgress < 0.25) {
      const t = scrollProgress / 0.25;
      targetCamPos.set(0 - t * 4, 11 - t * 4, 25 - t * 8);
      targetLookAt.set(0 + t * 2, 1, 0 + t * 1);
    } else if (scrollProgress < 0.5) {
      const t = (scrollProgress - 0.25) / 0.25;
      targetCamPos.set(-4 + t * 4, 7 - t * 1.5, 17 - t * 4);
      targetLookAt.set(2 - t * 2, 1 + t * 3, 1 - t * 1);
    } else if (scrollProgress < 0.75) {
      const t = (scrollProgress - 0.5) / 0.25;
      targetCamPos.set(0 + t * 6, 5.5 + t * 1.5, 13 + t * 3);
      targetLookAt.set(0, 4 + t * 0.4, 0);
    } else {
      const t = (scrollProgress - 0.75) / 0.25;
      targetCamPos.set(6 - t * 6, 7 + t * 4, 16 + t * 4);
      targetLookAt.set(0, 4.4 - t * 1.4, 0);
    }
  }, [scrollProgress]);

  return (
    <div className="three-fixed-scrolly-canvas">
      <div ref={mountRef} className="three-fullscreen-viewport" />
    </div>
  );
};
