echo "Enter yandex registry id:"
read -r yandex_registry_id
echo "Enter image tag:"
read -r image_tag
docker build -t place-recognition-mining-manager .
docker tag place-recognition-mining-manager "cr.yandex/$yandex_registry_id/place-recognition-mining-manager:$image_tag"
docker push "cr.yandex/$yandex_registry_id/place-recognition-mining-manager:$image_tag"
