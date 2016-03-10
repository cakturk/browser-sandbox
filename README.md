browser-sandbox
===============

chroot/nspawn jail altinda calisan browser
------------------------------------------
Bu proje firefox ya da istenen baska bir browseri chroot yardimi ile
izole bir ortam altinda calistirarak ilgili dizinlerin senkronizasyonunu
saglar. Bu sayede kullanicinin istenmeyen dosyalari web browser araciligi
ile upload etmesinin onune gecilir. Kullanicinin download ettigi dosyalar
ise yine ayni uygulama tarafindan, konfigurasyonda belirtilen (kullanicinin
yazma hakkina sahip oldugu) dizin altina senkronize edilir.

Kurulum
-------
Oncelikle bagimliklar kurulur

python-inotify bindingi icin;

```shell
pip install python-inotify

```
ya da

```shell
apt-get install python-inotify

```


```shell
apt-get install build-essential debootstrap git-core

# minimal rootfs olustur
mkdir firefoxfs
debootstrap --arch=amd64 jessie firefoxfs/

# chroot altinda firefox yukle
chroot path/to/firefoxfs
apt-get install -y --no-install-recommends iceweasel
exit # jailden cik

```
sandbox.ini ayar dosyasi
------------------------
Ayar dosyasini /etc/browser-sandbox/sandbox.ini ya da browser-sandbox.py
ile ayni dizin altina yerlestirebilirsiniz. ```/etc``` dizini altindaki
ayar daha oncelikli olarak islenecektir.

Ornek ayar dosyasi:

```ini
[default]
chroot=path/to/firefoxfs
cmdinchroot=firefox
# kaynak senkronizasyon dizini
syncsrcdir=path/to/firefoxfs/root/Downloads
# hedef senkronizasyon dizini
syncdstdir=/home/cakturk/dev/src/browser-sandbox/downloads

```

Linux interpreter yardimi ile calisan dosyalarda set-uid'ye izin
vermedigi icin uygulamayi set-uid biti set edilecek olan native bir
uygulama tarafindan calistiracagiz. Bu dosyayi build etmek icin;


```shell
make
su
chown root:root setuid-shim
chmod u+s setuid-shim
exit

```

Kullanim
--------

```shell
./setuid-shim

```
