import * as THREE from "three";
import type { ArchitectureNode } from "./data/model";

const colors = {
  external: 0x73d7ff,
  shared: 0xcaff00,
  market: 0xff6b4a,
  next: 0xd8afff,
} as const;

export class ArchitectureScene {
  readonly #container: HTMLElement;
  readonly #nodes: ArchitectureNode[];
  readonly #renderer: THREE.WebGLRenderer;
  readonly #scene = new THREE.Scene();
  readonly #camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  readonly #raycaster = new THREE.Raycaster();
  readonly #pointer = new THREE.Vector2();
  readonly #nodeMeshes: THREE.Mesh[] = [];
  readonly #clock = new THREE.Clock();
  readonly #reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  readonly #observer: ResizeObserver;
  #visible = true;
  #activeId = "market";

  constructor(container: HTMLElement, nodes: ArchitectureNode[], onSelect: (node: ArchitectureNode) => void) {
    this.#container = container;
    this.#nodes = nodes;
    this.#renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    this.#renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    this.#renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.#renderer.domElement.setAttribute("aria-label", "Interactive three-dimensional protocol architecture");
    this.#renderer.domElement.setAttribute("role", "img");
    this.#container.prepend(this.#renderer.domElement);

    this.#camera.position.set(0.5, 0.2, 18);
    this.#scene.fog = new THREE.FogExp2(0x071007, 0.027);

    this.#addAtmosphere();
    this.#addConnections();
    this.#addNodes();

    this.#observer = new ResizeObserver(() => this.#resize());
    this.#observer.observe(container);
    this.#resize();

    this.#renderer.domElement.addEventListener("pointermove", (event) => this.#point(event, false, onSelect));
    this.#renderer.domElement.addEventListener("click", (event) => this.#point(event, true, onSelect));
    this.#renderer.domElement.addEventListener("pointerleave", () => {
      this.#renderer.domElement.style.cursor = "grab";
    });

    const visibility = new IntersectionObserver(([entry]) => {
      this.#visible = entry?.isIntersecting ?? false;
    });
    visibility.observe(container);

    this.#animate();
  }

  select(id: string): void {
    this.#activeId = id;
    this.#nodeMeshes.forEach((mesh) => {
      const selected = mesh.userData.id === id;
      mesh.scale.setScalar(selected ? 1.28 : 1);
      const material = mesh.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = selected ? 2.4 : 1.15;
    });
  }

  #addAtmosphere(): void {
    const ambient = new THREE.AmbientLight(0xffffff, 0.65);
    const key = new THREE.PointLight(0xcaff00, 60, 24);
    key.position.set(-5, 5, 8);
    const fill = new THREE.PointLight(0x73d7ff, 45, 22);
    fill.position.set(7, -3, 6);
    this.#scene.add(ambient, key, fill);

    const geometry = new THREE.BufferGeometry();
    const points = new Float32Array(180 * 3);
    for (let i = 0; i < 180; i += 1) {
      points[i * 3] = (Math.random() - 0.5) * 23;
      points[i * 3 + 1] = (Math.random() - 0.5) * 12;
      points[i * 3 + 2] = (Math.random() - 0.5) * 8 - 2;
    }
    geometry.setAttribute("position", new THREE.BufferAttribute(points, 3));
    const material = new THREE.PointsMaterial({ color: 0xcaff00, size: 0.025, transparent: true, opacity: 0.36 });
    const particles = new THREE.Points(geometry, material);
    particles.name = "particles";
    this.#scene.add(particles);
  }

  #addConnections(): void {
    const byId = new Map(this.#nodes.map((node) => [node.id, node]));
    this.#nodes.forEach((node) => {
      node.connections.forEach((targetId) => {
        const target = byId.get(targetId);
        if (!target) return;
        const curve = new THREE.CatmullRomCurve3([
          new THREE.Vector3(...node.position),
          new THREE.Vector3((node.position[0] + target.position[0]) / 2, (node.position[1] + target.position[1]) / 2 + 0.45, -0.45),
          new THREE.Vector3(...target.position),
        ]);
        const geometry = new THREE.TubeGeometry(curve, 28, 0.025, 6, false);
        const material = new THREE.MeshBasicMaterial({ color: 0x7f9367, transparent: true, opacity: 0.62 });
        this.#scene.add(new THREE.Mesh(geometry, material));
      });
    });
  }

  #addNodes(): void {
    this.#nodes.forEach((node, index) => {
      const geometry = node.layer === "market"
        ? new THREE.IcosahedronGeometry(0.58, 1)
        : new THREE.SphereGeometry(0.46, 24, 18);
      const color = colors[node.layer];
      const material = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: node.id === this.#activeId ? 2.4 : 1.15,
        roughness: 0.28,
        metalness: 0.2,
        transparent: true,
        opacity: node.layer === "next" ? 0.62 : 0.96,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(...node.position);
      mesh.userData.id = node.id;
      mesh.userData.baseY = node.position[1];
      mesh.userData.phase = index * 0.72;
      if (node.id === this.#activeId) mesh.scale.setScalar(1.28);
      this.#nodeMeshes.push(mesh);
      this.#scene.add(mesh);
    });
  }

  #point(event: PointerEvent, commit: boolean, onSelect: (node: ArchitectureNode) => void): void {
    const bounds = this.#renderer.domElement.getBoundingClientRect();
    this.#pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    this.#pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
    this.#raycaster.setFromCamera(this.#pointer, this.#camera);
    const hit = this.#raycaster.intersectObjects(this.#nodeMeshes, false)[0];
    this.#renderer.domElement.style.cursor = hit ? "pointer" : "grab";
    if (!commit || !hit) return;
    const node = this.#nodes.find((candidate) => candidate.id === hit.object.userData.id);
    if (node) {
      this.select(node.id);
      onSelect(node);
    }
  }

  #resize(): void {
    const width = Math.max(this.#container.clientWidth, 1);
    const height = Math.max(this.#container.clientHeight, 1);
    this.#renderer.setSize(width, height, false);
    this.#camera.aspect = width / height;
    this.#camera.updateProjectionMatrix();
  }

  #animate = (): void => {
    requestAnimationFrame(this.#animate);
    if (!this.#visible && !this.#reduceMotion) return;
    const elapsed = this.#clock.getElapsedTime();
    if (!this.#reduceMotion) {
      this.#nodeMeshes.forEach((mesh) => {
        mesh.position.y = Number(mesh.userData.baseY) + Math.sin(elapsed * 0.72 + Number(mesh.userData.phase)) * 0.12;
        mesh.rotation.y = elapsed * 0.18;
      });
      const particles = this.#scene.getObjectByName("particles");
      if (particles) particles.rotation.z = elapsed * 0.012;
    }
    this.#renderer.render(this.#scene, this.#camera);
  };
}

export function canRenderWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}
