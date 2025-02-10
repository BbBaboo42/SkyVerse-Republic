if [ -z "$1" ]
  then
    echo "Please supply the version as an argument"
    exit
fi

mkdir -p versions/$1

wget https://github.com/bazelbuild/bazel/releases/download/$1/bazel_$1-linux-x86_64.deb -P versions/$1
wget https://github.com/bazelbuild/bazel/releases/download/$1/bazel-$1-linux-x86_64 -P versions/$1