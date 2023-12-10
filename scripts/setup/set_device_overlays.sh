cd /opt
sudo git clone https://github.com/libre-computer-project/libretech-wiring-tool.git

cd libretech-wiring-tool
sudo ./install.sh

sudo /opt/libretech-wiring-tool/ldto merge uart-a spi-cc-cs1 spi-cc-1cs-ili9341