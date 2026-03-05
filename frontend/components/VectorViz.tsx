"use client";

import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { VectorPoint, getSearchVectors } from "@/lib/api";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

interface Props {
  query: string;
  collection: string;
  limit?: number;
}

interface TooltipState {
  x: number;
  y: number;
  point: VectorPoint;
}

function normalize(values: number[]): number[] {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values.map((v) => (v - min) / range);
}

export function VectorViz({ query, collection, limit = 5 }: Props) {
  const [open, setOpen] = useState(false);
  const [points, setPoints] = useState<VectorPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{
    renderer: THREE.WebGLRenderer;
    controls: OrbitControls;
    animId: number;
    cleanup: () => void;
  } | null>(null);

  // Fetch vectors when panel opens
  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setPoints([]);
    getSearchVectors(query, collection, limit)
      .then(setPoints)
      .catch(() => setPoints([]))
      .finally(() => setLoading(false));
  }, [open, query, collection, limit]);

  useEffect(() => {
    if (!open || !mountRef.current || points.length < 2) return;

    const container = mountRef.current;
    const W = container.clientWidth || 560;
    const H = 340;

    // --- Scene ---
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xfafafa);
    scene.fog = new THREE.Fog(0xfafafa, 8, 20);

    const camera = new THREE.PerspectiveCamera(55, W / H, 0.1, 100);
    camera.position.set(0, 1.2, 4.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.07;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.6;
    controls.minDistance = 1.5;
    controls.maxDistance = 10;

    // --- Lighting ---
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 0.9);
    dir.position.set(4, 6, 4);
    scene.add(dir);

    // --- Compute 3D positions (x,y from PCA, z from certainty) ---
    const xs = points.map((p) => p.vector_2d[0]);
    const ys = points.map((p) => p.vector_2d[1]);
    const cs = points.map((p) => p.certainty ?? 0.5);
    const normX = normalize(xs);
    const normY = normalize(ys);
    const normZ = normalize(cs);
    const toCoord = (n: number) => (n - 0.5) * 3.2;

    // --- Axes helper (subtle) ---
    const axesGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-1.8, 0, 0), new THREE.Vector3(1.8, 0, 0),
      new THREE.Vector3(0, -1.8, 0), new THREE.Vector3(0, 1.8, 0),
      new THREE.Vector3(0, 0, -1.8), new THREE.Vector3(0, 0, 1.8),
    ]);
    const axesMat = new THREE.LineBasicMaterial({ color: 0x000000, opacity: 0.08, transparent: true });
    scene.add(new THREE.LineSegments(axesGeo, axesMat));

    // --- Result spheres ---
    const meshes: THREE.Mesh[] = [];
    points.forEach((p, i) => {
      const certainty = cs[i];
      const radius = 0.055 + certainty * 0.065;

      const geo = new THREE.SphereGeometry(radius, 24, 24);
      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(0xff00ff),
        emissive: new THREE.Color(0xff00ff),
        emissiveIntensity: 0.08 + certainty * 0.18,
        roughness: 0.35,
        metalness: 0.05,
        transparent: true,
        opacity: 0.45 + certainty * 0.45,
        depthWrite: false,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(toCoord(normX[i]), toCoord(normY[i]), toCoord(normZ[i]));
      mesh.userData = { point: p };
      scene.add(mesh);
      meshes.push(mesh);

      // Line from origin to sphere
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        mesh.position.clone(),
      ]);
      const lineMat = new THREE.LineBasicMaterial({
        color: 0xff00ff,
        opacity: 0.08 + certainty * 0.22,
        transparent: true,
      });
      scene.add(new THREE.Line(lineGeo, lineMat));
    });

    // --- Query node (yellow box, spinning) ---
    const qGeo = new THREE.BoxGeometry(0.18, 0.18, 0.18);
    const qMat = new THREE.MeshStandardMaterial({
      color: 0xffff00,
      emissive: 0xffff00,
      emissiveIntensity: 0.25,
      roughness: 0.2,
    });
    const qMesh = new THREE.Mesh(qGeo, qMat);
    qMesh.position.set(0, 0, 0);
    scene.add(qMesh);

    // Subtle ring around query node
    const ringGeo = new THREE.RingGeometry(0.22, 0.26, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x000000,
      opacity: 0.12,
      transparent: true,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    scene.add(ring);

    // --- Raycaster for hover ---
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    raycaster.params.Points = { threshold: 0.1 };

    const onMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);

      const hits = raycaster.intersectObjects(meshes);
      if (hits.length > 0) {
        const point = hits[0].object.userData.point as VectorPoint;
        setTooltip({ x: e.clientX - rect.left, y: e.clientY - rect.top, point });
        controls.autoRotate = false;
        document.body.style.cursor = "pointer";
      } else {
        setTooltip(null);
        controls.autoRotate = true;
        document.body.style.cursor = "";
      }
    };

    const onMouseLeave = () => {
      setTooltip(null);
      controls.autoRotate = true;
      document.body.style.cursor = "";
    };

    renderer.domElement.addEventListener("mousemove", onMouseMove);
    renderer.domElement.addEventListener("mouseleave", onMouseLeave);

    // --- Resize ---
    const ro = new ResizeObserver(() => {
      const w = container.clientWidth;
      camera.aspect = w / H;
      camera.updateProjectionMatrix();
      renderer.setSize(w, H);
    });
    ro.observe(container);

    // --- Animate ---
    let animId = 0;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      qMesh.rotation.y += 0.012;
      qMesh.rotation.x += 0.006;
      ring.rotation.z += 0.004;
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    sceneRef.current = {
      renderer,
      controls,
      animId,
      cleanup: () => {
        cancelAnimationFrame(animId);
        ro.disconnect();
        renderer.domElement.removeEventListener("mousemove", onMouseMove);
        renderer.domElement.removeEventListener("mouseleave", onMouseLeave);
        document.body.style.cursor = "";
        scene.traverse((obj) => {
          if (obj instanceof THREE.Mesh) {
            obj.geometry.dispose();
            if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
            else obj.material.dispose();
          }
        });
        renderer.dispose();
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      },
    };

    return () => sceneRef.current?.cleanup();
  }, [open, points]);

  return (
    <div className="mt-3">
      <motion.button
        onClick={() => setOpen((o) => !o)}
        className="neo-button text-xs py-1 px-3 border-2"
        style={{ boxShadow: "2px 2px 0px 0px #000000" }}
        whileHover={{ y: -2, boxShadow: "4px 6px 0px 0px #000000" }}
        whileTap={{ y: 2, boxShadow: "0px 0px 0px 0px #000000" }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
      >
        <span>{open ? "▾" : "▸"}</span>{" "}
        <span>{open ? "Hide 3D vector space" : "Show 3D vector space"}</span>
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 28 }}
            className="overflow-hidden"
          >
            <div className="neo-panel p-3 mt-2">
              <div className="flex items-center justify-between mb-2">
                <p className="data-label">3D semantic space — drag to rotate · scroll to zoom</p>
                <div className="flex items-center gap-3 text-[9px] font-mono opacity-50">
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-3 border-2 border-black bg-[#ffff00]" />
                    query (origin)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: "rgba(255,0,255,0.7)" }} />
                    result (size &amp; z = certainty)
                  </span>
                </div>
              </div>

              {/* Three.js canvas mount point */}
              <div ref={mountRef} className="relative w-full" style={{ height: 340 }}>
                {loading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-[#fafafa]">
                    <span className="font-mono text-xs opacity-50 uppercase animate-pulse">Loading vectors…</span>
                  </div>
                )}
                {!loading && points.length < 2 && (
                  <div className="absolute inset-0 flex items-center justify-center bg-[#fafafa]">
                    <span className="font-mono text-xs opacity-50 uppercase">Not enough vector data</span>
                  </div>
                )}
                {/* Hover tooltip */}
                {tooltip && (
                  <div
                    className="absolute z-30 bg-black text-white font-mono text-[9px] p-2 pointer-events-none animate-fade-in"
                    style={{
                      left: tooltip.x + 14,
                      top: tooltip.y - 10,
                      whiteSpace: "nowrap",
                      minWidth: 130,
                    }}
                  >
                    <div className="font-bold uppercase truncate max-w-[180px]">{tooltip.point.title}</div>
                    <div style={{ color: "#ff00ff" }}>
                      {((tooltip.point.certainty ?? 0) * 100).toFixed(1)}% match
                    </div>
                    {tooltip.point.distance != null && (
                      <div className="opacity-50">dist: {tooltip.point.distance.toFixed(3)}</div>
                    )}
                    {tooltip.point.country && (
                      <div className="opacity-70">{tooltip.point.country}</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
