# Restaurar herramientas en un contenedor nuevo
Si /home/claude/canal no existe (contenedor nuevo):
```
S=/tmp/claude-0/-home-claude/3f8f79a9-c46c-53fb-baec-2bfb3165bcc1/scratchpad
mkdir -p $S/music /home/claude/canal/web/deploy /home/claude/canal/short/miniaturas /home/claude/canal/video4
cp herramientas/motor/*.py herramientas/motor/*.json $S/ ; cp herramientas/motor/nebula.mp3 $S/music/
cp herramientas/web/* /home/claude/canal/web/ ; cp -r web/. /home/claude/canal/web/deploy/
cp herramientas/marca/*.png /home/claude/canal/ ; cp herramientas/video4/* /home/claude/canal/video4/
mkdir -p /home/claude/canal/short/nvda && cp herramientas/nvda/*.jpg /home/claude/canal/short/nvda/
```
Las rutas de los scripts están fijadas a esas carpetas. Fuentes Inter en /usr/share/fonts/opentype/inter (si faltan: apt/pip fonts-inter).
