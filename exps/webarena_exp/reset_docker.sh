# stop the dockers
docker stop shopping_admin forum gitlab shopping
# remove the docker images
docker rm shopping_admin forum gitlab shopping

# restart the dockers
docker load --input shopping_final_0712.tar
docker load --input shopping_admin_final_0719.tar
docker load --input postmill-populated-exposed-withimg.tar
docker load --input gitlab-populated-final-port8023.tar
docker run --name shopping -p 7770:80 -d shopping_final_0712
docker run --name shopping_admin -p 7780:80 -d shopping_admin_final_0719
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg
docker run --name gitlab -d -p 8023:8023 gitlab-populated-final-port8023 /opt/gitlab/embedded/bin/runsvdir-start

# Note: 
YOUR_DATA_DIR="<YOUR_DATA_DIR>"
docker run -d --name=wikipedia --volume=${YOUR_DATA_DIR}:/data -p 8888:80 ghcr.io/kiwix/kiwix-serve:3.3.0 wikipedia_en_all_maxi_2022-05.zim

# run the web servers
sleep 120

docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7770" # no trailing slash
docker exec shopping mysql -u magentouser -pMyPassword magentodb -e  'UPDATE core_config_data SET value="http://localhost:7770/" WHERE path = "web/secure/base_url";'
docker exec shopping /var/www/magento2/bin/magento cache:flush

docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7780" # no trailing slash
docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e  'UPDATE core_config_data SET value="http://localhost:7780/" WHERE path = "web/secure/base_url";'
docker exec shopping_admin /var/www/magento2/bin/magento cache:flush

docker exec gitlab sed -i "s/^external_url.*/external_url 'http://localhost:8023'/"  /etc/gitlab/gitlab.rb
docker exec gitlab gitlab-ctl reconfigure

