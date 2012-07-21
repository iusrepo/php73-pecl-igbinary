%{!?__pecl: %{expand: %%global __pecl %{_bindir}/pecl}}
%{!?php_extdir: %{expand: %%global php_extdir %(php-config --extension-dir)}}

%global extname   igbinary
%global gitver    3b8ab7e
%global prever    -dev

%if 0%{?fedora} >= 14
%global withapc 1
%else
# EL-6 only provides 3.1.3pl1
%global withapc 0
%endif

Summary:        Replacement for the standard PHP serializer
Name:           php-pecl-igbinary
Version:        1.1.2
%if 0%{?gitver:1}
Release:	0.3.git%{gitver}%{?dist}
Source0:	igbinary-igbinary-1.1.1-15-g3b8ab7e.tar.gz
%else
Release:        2%{?dist}
Source0:        http://pecl.php.net/get/%{extname}-%{version}.tgz
# https://bugs.php.net/59668
Source1:        %{extname}-tests.tgz
%endif
# https://bugs.php.net/59669
License:        BSD
Group:          System Environment/Libraries

URL:            http://pecl.php.net/package/igbinary

# https://bugs.php.net/60298
Patch0:         igbinary-php54.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
BuildRequires:  php-devel >= 5.2.0
%if %{withapc}
BuildRequires:  php-pecl-apc-devel >= 3.1.7
%else
BuildRequires:  php-pear
%endif

Requires(post): %{__pecl}
Requires(postun): %{__pecl}
Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
Provides:       php-pecl(%{extname}) = %{version}

# RPM 4.8
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
# RPM 4.9
%global __provides_exclude_from %{?__provides_exclude_from:%__provides_exclude_from|}%{_libdir}/.*\\.so$


%description
Igbinary is a drop in replacement for the standard PHP serializer.

Instead of time and space consuming textual representation, 
igbinary stores PHP data structures in a compact binary form. 
Savings are significant when using memcached or similar memory
based storages for serialized data.


%package devel
Summary:       Igbinary developer files (header)
Group:         Development/Libraries
Requires:      php-pecl-%{extname}%{?_isa} = %{version}-%{release}
Requires:      php-devel

%description devel
These are the files needed to compile programs using Igbinary


%prep
%setup -q -c

%if 0%{?gitver:1}
mv igbinary-igbinary-%{gitver}/package.xml .
mv igbinary-igbinary-%{gitver} %{extname}-%{version}
cd %{extname}-%{version}
%patch0 -p0 -b .php54

%else
cd %{extname}-%{version}
tar xzf %{SOURCE1}

%endif

# Check version
extver=$(sed -n '/#define IGBINARY_VERSION/{s/.* "//;s/".*$//;p}' igbinary.h)
if test "x${extver}" != "x%{version}%{?prever}"; then
   : Error: Upstream version is ${extver}, expecting %{version}%{?prever}.
   exit 1
fi
cd ..

cat <<EOF | tee %{extname}.ini
; Enable %{extname} extension module
extension=%{extname}.so

; Enable or disable compacting of duplicate strings
; The default is On.
;igbinary.compact_strings=On

; Use igbinary as session serializer
;session.serialize_handler=igbinary

%if %{withapc}
; Use igbinary as APC serializer
;apc.serializer=igbinary
%endif
EOF

cp -r %{extname}-%{version} %{extname}-%{version}-zts


%build
cd %{extname}-%{version}
%{_bindir}/phpize
%configure --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if 0%{?__ztsphp:1}
cd ../%{extname}-%{version}-zts
%{_bindir}/zts-phpize
%configure --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
rm -rf %{buildroot}

make install -C %{extname}-%{version} \
     INSTALL_ROOT=%{buildroot}

install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

install -D -m 644 %{extname}.ini %{buildroot}%{_sysconfdir}/php.d/%{extname}.ini

# Install the ZTS stuff
%if 0%{?__ztsphp:1}
make install -C %{extname}-%{version}-zts \
     INSTALL_ROOT=%{buildroot}
install -D -m 644 %{extname}.ini %{buildroot}%{php_ztsinidir}/%{extname}.ini
%endif


%check
# simple module load test
# without APC to ensure than can run without
%{_bindir}/php --no-php-ini \
    --define extension_dir=%{extname}-%{version}/modules \
    --define extension=%{extname}.so \
    --modules | grep %{extname}

%{_bindir}/zts-php --no-php-ini \
    --define extension_dir=%{extname}-%{version}-zts/modules \
    --define extension=%{extname}.so \
    --modules | grep %{extname}

cd %{extname}-%{version}
%if %{withapc}
# APC required for test 045
ln -s %{php_extdir}/apc.so modules/
%endif

NO_INTERACTION=1 make test | tee rpmtests.log
# https://bugs.php.net/60298
# grep -q "FAILED TEST" rpmtests.log && exit 1


%clean
rm -rf %{buildroot}


%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{extname} >/dev/null || :
fi


%files
%defattr(-,root,root,-)
%doc %{extname}-%{version}/COPYING
%doc %{extname}-%{version}/CREDITS
%doc %{extname}-%{version}/NEWS
%doc %{extname}-%{version}/README
%config(noreplace) %{_sysconfdir}/php.d/%{extname}.ini
%{php_extdir}/%{extname}.so
%{pecl_xmldir}/%{name}.xml
%if 0%{?__ztsphp:1}
%{php_ztsextdir}/%{extname}.so
%config(noreplace) %{php_ztsinidir}/%{extname}.ini
%endif


%files devel
%defattr(-,root,root,-)
%{_includedir}/php/ext/%{extname}
%if 0%{?__ztsphp:1}
%{php_ztsincldir}/ext/%{extname}
%endif


%changelog
* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.3.git3b8ab7e
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Apr 23 2012 Collet <remi@fedoraproject.org> - 1.1.2-0.2.git3b8ab7e
- enable ZTS extension

* Fri Jan 20 2012 Collet <remi@fedoraproject.org> - 1.1.2-0.1.git3b8ab7e
- update to git snapshot for php 5.4

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Sep 18 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-3
- fix EPEL-6 build, no arch version for php-devel

* Sat Sep 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-2
- clean spec, adapted filters

* Mon Mar 14 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- version 1.1.1 published on pecl.php.net
- rename to php-pecl-igbinary

* Mon Jan 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- update to 1.1.1

* Fri Dec 31 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-3
- updated tests from Git.

* Sat Oct 23 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-2
- filter provides to avoid igbinary.so
- add missing %%dist

* Wed Sep 29 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-1
- initital RPM

