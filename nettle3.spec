%global optflags %{optflags} -O3

%bcond_with bootstrap

# (tpg) enable PGO build
%bcond_without pgo

%define major 8
%define hogweedmajor 6
%define libname %mklibname nettle %{major}
%define libhogweed %mklibname hogweed %{hogweedmajor}

Summary:	Nettle 3.x cryptographic library (runtime compat)
Name:		nettle3
Epoch:		1
Version:	3.10.2
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		https://www.lysator.liu.se/~nisse/nettle/
Source0:	https://ftp.gnu.org/gnu/nettle/nettle-%{version}.tar.gz
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	libtool-base
BuildRequires:	slibtool
BuildRequires:	make
BuildRequires:	recode
BuildRequires:	gmp-devel
BuildRequires:	texinfo
%ifnarch riscv64
BuildRequires:	pkgconfig(valgrind)
%endif
%if %{with bootstrap}
BuildRequires:	pkgconfig(openssl)
%endif

Requires:	%{libname} = %{EVRD}
Requires:	%{libhogweed} = %{EVRD}

%description
Nettle 3.x shared libraries (libnettle.so.%{major} and
libhogweed.so.%{hogweedmajor}) so binaries built against Nettle 3
keep working after the 4.0 soname bump. New builds should use nettle 4.

%files
%doc AUTHORS ChangeLog

#----------------------------------------------------------------------------

%package -n %{libname}
Summary:	Nettle 3.x shared library
Group:		System/Libraries

%description -n %{libname}
This is the shared library part of the Nettle 3.x library.

%files -n %{libname}
%{_libdir}/libnettle.so.%{major}*

#----------------------------------------------------------------------------

%if !%{with bootstrap}
%package -n %{libhogweed}
Summary:	Hogweed 3.x shared library
Group:		System/Libraries

%description -n %{libhogweed}
This is the shared library part of the Hogweed 3.x library.

%files -n %{libhogweed}
%{_libdir}/libhogweed.so.%{hogweedmajor}*
%endif

%prep
%autosetup -p1 -n nettle-%{version}
%config_update
# Disable -ggdb3 which makes debugedit unhappy
sed s/ggdb3/g/ -i configure

%build
export CONFIGURE_TOP="$(pwd)"

mkdir -p bfd
ln -s %{_bindir}/ld.bfd bfd/ld
export PATH=$PWD/bfd:$PATH

# enable-x86-aesni without enable-fat likely causes bug 2408

mkdir build
cd build

%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate -mllvm -vp-counters-per-site=8" \
CXXFLAGS="%{optflags} -fprofile-generate" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%configure \
	--enable-static \
	--disable-openssl \
%ifarch %{arm} %{aarch64}
	--enable-arm-neon \
%endif
%ifarch %{x86_64}
	--enable-x86-aesni \
%ifnarch znver1
	--enable-fat \
%endif
%endif
	--enable-shared

%make_build
make check ||:

unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw

make clean

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%configure \
	--enable-static \
	--disable-openssl \
	--disable-x86-sha-ni \
%ifarch %{arm} %{aarch64}
	--enable-arm-neon \
%endif
%ifarch %{x86_64}
	--enable-x86-aesni \
%ifnarch znver1
	--enable-fat \
%endif
%endif
	--enable-shared

%make_build

%if ! %{cross_compiling}
%check
%make_build check -C build
%endif

%install
%make_install -C build
recode ISO-8859-1..UTF-8 ChangeLog

# (tpg) strip LTO from "LLVM IR bitcode" files
check_convert_bitcode() {
    printf '%s\n' "Checking for LLVM IR bitcode"
    llvm_file_name=$(realpath ${1})
    llvm_file_type=$(file ${llvm_file_name})

    if printf '%s\n' "${llvm_file_type}" | grep -q "LLVM IR bitcode"; then
# recompile without LTO
    clang %{optflags} -fno-lto -Wno-unused-command-line-argument -x ir ${llvm_file_name} -c -o ${llvm_file_name}
    elif printf '%s\n' "${llvm_file_type}" | grep -q "current ar archive"; then
    printf '%s\n' "Unpacking ar archive ${llvm_file_name} to check for LLVM bitcode components."
# create archive stage for objects
    archive_stage=$(mktemp -d)
    archive=${llvm_file_name}
    cd ${archive_stage}
    ar x ${archive}
    for archived_file in $(find -not -type d); do
        check_convert_bitcode ${archived_file}
        printf '%s\n' "Repacking ${archived_file} into ${archive}."
        ar r ${archive} ${archived_file}
    done
    ranlib ${archive}
    cd ..
    fi
}

for i in $(find %{buildroot} -type f -name "*.[ao]"); do
    check_convert_bitcode ${i}
done

# do not compete with nettle 4 headers, pkgconfig, tools, or unversioned .so
rm -rf \
	%{buildroot}%{_bindir} \
	%{buildroot}%{_includedir} \
	%{buildroot}%{_infodir} \
	%{buildroot}%{_mandir} \
	%{buildroot}%{_libdir}/pkgconfig
rm -f \
	%{buildroot}%{_libdir}/*.a \
	%{buildroot}%{_libdir}/libnettle.so \
	%{buildroot}%{_libdir}/libhogweed.so
