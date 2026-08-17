# Runtime-only 3.x sonames so existing binaries keep working after nettle 4.0.
# Do not ship headers, pkgconfig, unversioned .so, or tools — those belong to nettle 4.

%ifarch %{x86_64}
%bcond_without compat32
%endif

%define major 8
%define hogweedmajor 6
%define libname %mklibname nettle %{major}
%define libhogweed %mklibname hogweed %{hogweedmajor}
%define lib32name %mklib32name nettle %{major}
%define lib32hogweed %mklib32name hogweed %{hogweedmajor}

Summary:	Nettle 3.x cryptographic libraries (runtime compat)
Name:		nettle3
Version:	3.10.2
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		https://www.lysator.liu.se/~nisse/nettle/
Source0:	https://ftp.gnu.org/gnu/nettle/nettle-%{version}.tar.gz
BuildSystem:	autotools
BuildOption:	--disable-documentation
BuildOption:	--disable-openssl
BuildOption:	--enable-shared
%ifarch %{arm} %{aarch64}
BuildOption:	--enable-arm-neon
%endif
%ifarch %{x86_64}
BuildOption:	--enable-x86-aesni
BuildOption:	--disable-x86-sha-ni
%ifnarch znver1
BuildOption:	--enable-fat
%endif
%endif
BuildRequires:	gmp-devel
%if %{with compat32}
BuildRequires:	devel(libgmp)
%endif

Requires:	%{libname} = %{EVRD}
Requires:	%{libhogweed} = %{EVRD}

%description
Nettle 3.x shared libraries (libnettle.so.%{major} and
libhogweed.so.%{hogweedmajor}). This package exists so binaries built
against Nettle 3 keep working after the Nettle 4.0 soname bump.
New builds should use nettle 4.

%files
%license COPYING.LESSERv3 COPYINGv2
%doc AUTHORS NEWS

#----------------------------------------------------------------------------

%package -n %{libname}
Summary:	Nettle 3.x shared library
Group:		System/Libraries

%description -n %{libname}
libnettle.so.%{major} from Nettle %{version}, for binaries built
against Nettle 3.

%files -n %{libname}
%{_libdir}/libnettle.so.%{major}*

#----------------------------------------------------------------------------

%package -n %{libhogweed}
Summary:	Hogweed 3.x shared library
Group:		System/Libraries

%description -n %{libhogweed}
libhogweed.so.%{hogweedmajor} from Nettle %{version}, for binaries
built against Nettle 3.

%files -n %{libhogweed}
%{_libdir}/libhogweed.so.%{hogweedmajor}*

#----------------------------------------------------------------------------

%if %{with compat32}
%package -n %{lib32name}
Summary:	Nettle 3.x shared library (32-bit)
Group:		System/Libraries

%description -n %{lib32name}
32-bit libnettle.so.%{major} from Nettle %{version}.

%files -n %{lib32name}
%{_prefix}/lib/libnettle.so.%{major}*

#----------------------------------------------------------------------------

%package -n %{lib32hogweed}
Summary:	Hogweed 3.x shared library (32-bit)
Group:		System/Libraries

%description -n %{lib32hogweed}
32-bit libhogweed.so.%{hogweedmajor} from Nettle %{version}.

%files -n %{lib32hogweed}
%{_prefix}/lib/libhogweed.so.%{hogweedmajor}*
%endif

%prep
%autosetup -p1 -n nettle-%{version}
# Disable -ggdb3 which makes debugedit unhappy
sed s/ggdb3/g/ -i configure

%if ! %{cross_compiling}
%check
%make_build check -C _OMV_rpm_build
%endif

%install -a
# runtime sonames only — do not compete with nettle 4
rm -rf \
	%{buildroot}%{_bindir} \
	%{buildroot}%{_includedir} \
	%{buildroot}%{_infodir} \
	%{buildroot}%{_mandir} \
	%{buildroot}%{_libdir}/pkgconfig \
	%{buildroot}%{_prefix}/lib/pkgconfig
rm -f \
	%{buildroot}%{_libdir}/*.a \
	%{buildroot}%{_libdir}/libnettle.so \
	%{buildroot}%{_libdir}/libhogweed.so \
	%{buildroot}%{_prefix}/lib/*.a \
	%{buildroot}%{_prefix}/lib/libnettle.so \
	%{buildroot}%{_prefix}/lib/libhogweed.so
