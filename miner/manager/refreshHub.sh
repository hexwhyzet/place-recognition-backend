#echo "Enter yandex registry id:"
#read -r yandex_registry_id
echo "Enter image tag:"
read -r image_tag
cd ../../
docker build -t place-recognition-mining-manager -f miner/manager/Dockerfile .
docker tag place-recognition-mining-manager "cr.yandex/crpktc7jeim3h82e69hv/place-recognition-mining-manager:$image_tag"
docker push "cr.yandex/crpktc7jeim3h82e69hv/place-recognition-mining-manager:$image_tag"
