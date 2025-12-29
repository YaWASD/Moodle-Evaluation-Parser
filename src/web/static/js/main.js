document.addEventListener("DOMContentLoaded", () => {
    console.log("Веб-интерфейс загружен.");
    document.querySelectorAll(".flash").forEach((node) => {
        setTimeout(() => {
            node.style.opacity = "0";
            setTimeout(() => node.remove(), 400);
        }, 4000);
    });

    // Upload page: show selected XML filename before submit
    const fileInput = document.getElementById("xml-file-input");
    const fileNameNode = document.getElementById("selected-file-name");
    const dropzone = fileInput ? fileInput.closest(".dropzone") : null;

    const setFileName = (name) => {
        if (!fileNameNode) return;
        fileNameNode.textContent = name && String(name).trim() ? `Выбран файл: ${name}` : "Файл не выбран";
    };

    const setFileList = (files) => {
        if (!fileNameNode) return;
        if (!files || !files.length) {
            fileNameNode.textContent = "Файл не выбран";
            return;
        }
        const names = Array.from(files).map((f) => f && f.name).filter(Boolean);
        fileNameNode.textContent =
            names.length === 1 ? `Выбран файл: ${names[0]}` : `Выбрано файлов: ${names.length} — ${names.join(", ")}`;
    };

    if (fileInput) {
        fileInput.addEventListener("change", () => {
            setFileList(fileInput.files);
        });
    }

    // Best-effort drag & drop visual feedback + filename (without breaking older browsers)
    if (dropzone && fileInput) {
        const stop = (e) => {
            e.preventDefault();
            e.stopPropagation();
        };

        ["dragenter", "dragover"].forEach((ev) => {
            dropzone.addEventListener(ev, (e) => {
                stop(e);
                dropzone.classList.add("dropzone--active");
            });
        });
        ["dragleave", "drop"].forEach((ev) => {
            dropzone.addEventListener(ev, (e) => {
                stop(e);
                dropzone.classList.remove("dropzone--active");
            });
        });

        dropzone.addEventListener("drop", (e) => {
            const files = e.dataTransfer && e.dataTransfer.files;
            if (!files || !files.length) return;
            setFileList(files);

            // Try to attach dropped file to input (works in Chromium; may fail in some browsers)
            try {
                const dt = new DataTransfer();
                Array.from(files).forEach((f) => dt.items.add(f));
                fileInput.files = dt.files;
            } catch (_) {
                // ignore
            }
        });
    }
});

