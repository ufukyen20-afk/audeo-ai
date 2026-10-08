/*! coi-serviceworker v0.1.7 - Guido Zouffrej | MIT License */
(() => {
    const n = window.location;
    if ("serviceWorker" in navigator) {
        if (window.crossOriginIsolated) {
            console.log("COOP/COEP isolation active via coi-serviceworker.");
        } else {
            navigator.serviceWorker.register(window.document.currentScript.src).then(
                (e) => {
                    e.addEventListener("updatefound", () => {
                        window.location.reload();
                    });
                    if (e.active && !navigator.serviceWorker.controller) {
                        window.location.reload();
                    }
                },
                (e) => {
                    console.error("COOP/COEP Service Worker registration failed:", e);
                }
            );
        }
    }
})();


if ("undefined" != typeof WorkerGlobalScope && self instanceof WorkerGlobalScope) {
    self.addEventListener("install", () => self.skipWaiting());
    self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));


    self.addEventListener("fetch", (e) => {
        const { request: r } = e;
        if (r.cache === "only-if-cached" && r.mode !== "same-origin") {
            return;
        }


        e.respondWith(
            fetch(r).then((response) => {
                if (response.status === 0) {
                    return response;
                }


                const newHeaders = new Headers(response.headers);
                newHeaders.set("Cross-Origin-Embedder-Policy", "require-corp");
                newHeaders.set("Cross-Origin-Opener-Policy", "same-origin");


                return new Response(response.body, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: newHeaders,
                });
            }).catch((err) => console.error(err))
        );
    });
}

