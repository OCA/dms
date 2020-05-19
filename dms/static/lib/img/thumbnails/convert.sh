for f in *.svg; do
  inkscape $f -d 300 -e ${f%.*}.png
done