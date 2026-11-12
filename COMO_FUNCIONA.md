# Cómo publicar sin el ordenador del usuario

1. **Descargar audio/imágenes** (el contenedor no llega a esas webs): crear `descargas/<carpeta>.json` con `{"nombre.ext": "https://url"}`, hacer push, esperar ~30 s, `git pull` → archivos en `descargas/<carpeta>/`.
2. **Subir vídeo**: carpeta `cola/AAAA-MM-DD_nombre/` con `video.mp4`, `mini.jpg` y `meta.json`
   (`titulo`, `descripcion`, `tags`, `categoria` "25", `privacidad` "private", `miniatura` "mini.jpg"). Push → GitHub Actions lo sube en PRIVADO y deja `resultado.json` con el id (`git pull` para leerlo). El mp4 se borra del repo tras subirlo.
   Mientras la app no pase la auditoría de YouTube, los vídeos quedan en privado: avisar al usuario con el enlace para que lo publique desde YouTube Studio en el móvil.
3. **Web**: copiar `/home/claude/canal/web/deploy/.` en `web/` y hacer push → se publica sola en comovaelmundo.pages.dev.
Comprobar el estado en https://github.com/ByMateos/comovaelmundo/actions (solo lectura) o leyendo los archivos tras `git pull`.
