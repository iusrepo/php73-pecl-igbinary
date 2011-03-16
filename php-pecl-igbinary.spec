%{!?__pecl: %{expand: %%global __pecl %{_bindir}/pecl}}
%{!?php_extdir: %{expand: %%global php_extdir %(php-config --extension-dir)}}

%global    extname   igbinary

Summary:        Replacement for the standard PHP serializer
Name:           php-pecl-igbinary
Version:        1.1.1
Release:        1%{?dist}
License:        BSD
Group:          System Environment/Libraries

URL:            http://pecl.php.net/package/igbinary
Source0:        http://pecl.php.net/get/%{extname}-%{version}.tgz
# http://pecl.php.net/bugs/22598
# https://github.com/igbinary/igbinary/tree/1.1.1/tests
Source1:        %{extname}-tests.tgz

BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
BuildRequires:  php-devel >= 5.2.0
BuildRequires:  php-pecl-apc-devel >= 3.1.7

Requires(post): %{__pecl}
Requires(postun): %{__pecl}
Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
Provides:       php-pecl(%{extname}) = %{version}


%{?filter_setup:
%filter_provides_in %{php_extdir}/.*\.so$
%filter_setup
}


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
Requires:      php-devel%{?_isa}

%description devel
These are the files needed to compile programs using Igbinary


%prep
%setup -q -c
cd %{extname}-%{version}
%{__tar} xzf %{SOURCE1}

%build
cd %{extname}-%{version}
%{_bindir}/phpize
%{configure} --with-php-config=%{_bindir}/php-config
%{__make} %{?_smp_mflags}


%install
%{__rm} -rf %{buildroot}

%{__mkdir_p} %{buildroot}%{pecl_xmldir}
%{__install} -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

cd %{extname}-%{version}
%{__make} install INSTALL_ROOT=%{buildroot}

%{__mkdir} -p %{buildroot}%{_sysconfdir}/php.d/
%{__cat} > %{buildroot}%{_sysconfdir}/php.d/%{extname}.ini <<EOF
; Enable %{extname} extension module
extension=%{extname}.so

; Enable or disable compacting of duplicate strings
; The default is On.
;igbinary.compact_strings=On

; Use igbinary as session serializer
;session.serialize_handler=igbinary

; Use igbinary as APC serializer
;apc.serializer=igbinary
EOF


%check
cd %{extname}-%{version}

# simple module load test
# without APC to ensure than can run without
%{_bindir}/php --no-php-ini \
    --define extension_dir=modules \
    --define extension=%{extname}.so \
    --modules | grep %{extname}

# APC required for test 045
%{__ln_s} %{php_extdir}/apc.so modules/

NO_INTERACTION=1 %{__make} test | tee rpmtests.log
grep -q "FAILED TEST" rpmtests.log && exit 1


%clean
%{__rm} -rf %{buildroot}


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


%files devel
%defattr(-,root,root,-)
%{_includedir}/php/ext/%{extname}


%changelog
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

