virt-install --connect qemu:///system                  \
  --name rhfs01.prolo                                  \
  --memory 2048                                        \
  --vcpus=2,maxvcpus=4                                 \
  --cpu host                                           \
  --disk size=40                                       \
  --disk size=40                                       \
  --network bridge=br-prolo                            \
  --network bridge=br-prolo                            \
  --pxe                                                \
  --virt-type kvm                                      \
  --graphics spice                                     \
  --os-variant centos7.0
