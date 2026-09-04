FAIL_NO_SINGLE_INSTANCE

### Candidate Table

| Manufacturer | Model / SKU / Family | Direct First-Party Product URL | Direct First-Party Datasheet URL | Exact First-Party Binding Sentence | Evaluation Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Intel Corporation** | 800G DR8 Transmitter PIC (MM# 94814) / 800G 2xFR4 Transmitter PIC (MM# 94811) / Reference Model SPTSRS3PNCDF | `https://www.intel.com` | Material Declaration Data Sheets (MDDS MM# 94814, MM# 94811) via `https://www.intel.com` | *None* (MDDS documents cover bare component PICs; no full transceiver commercial product datasheet exists with an explicit SiPh binding sentence). | **FAIL** (Component/demo only; no commercial transceiver SKU datasheet) |
| **Jabil Inc.** | 800G OSFP 2xFR4 Optical Transceiver | `https://www.jabil.com/industries/telecommunications-networking/photonics.html` | `https://www.jabil.com` (800G OSFP 2xFR4 Product Overview) | *None* (First-party product documentation omits "silicon photonics"; SiPh is mentioned only in corporate capability overviews and partner press releases). | **FAIL** (Missing product-level binding sentence in first-party documentation) |
| **Cisco Systems, Inc.** | OSFP-800G-DR8 / QDD-800G-DR8-S | `https://www.cisco.com/c/en/us/products/interfaces-modules/transceiver-modules/index.html` | `https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/osfp-800g-transceiver-modules-ds.html` | *None* (Datasheet strictly specifies optical/electrical interfaces and standards compliance; the word "photonics" is entirely absent from the document). | **FAIL** (Datasheet omits optical implementation technology) |
| **Acacia (Cisco Systems)** | Acacia 800ZR / 800G ZR+ (Delphi Generation) | `https://www.acacia-inc.com` | *None* (Public downloadable datasheet URL is not published/un-gated) | *None* (SiPh PIC and 3D Siliconization are described in corporate blog posts/press releases, but no open-access commercial product datasheet exists). | **FAIL** (No publicly accessible first-party datasheet; platform-level claims only) |
| **Marvell Technology, Inc.** | COLORZ 800 Family (800ZR / 800G ZR+) | `https://www.marvell.com/products/optical-interconnect/data-center-interconnect-modules.html` | *None* (HTTP 403 access restricted / gated customer portal) | *None* (Family-level descriptions link COLORZ 800 to Orion DSP + SiPho platform, but no open individual commercial SKU datasheet is retrievable). | **FAIL** (Access-restricted / login-gated; family-level platform statements only) |
| **Coherent Corp.** | 800G-DR8 / FTCE Series (e.g. FTCE4516, FTCE4527) | `https://www.coherent.com` | `https://www.coherent.com` (FTCE product documentation) | *None* (SiPh is discussed in corporate technology whitepapers/articles, but commercial 800G datasheets omit SiPh binding or use EML/InP platforms). | **FAIL** (No first-party commercial datasheet binding specific SKU to SiPh) |
| **Eoptolink Technology Inc.** | EOLO-138HG-5H-SM (OSFP) / EOLD-138HG-5H-SM (QSFP-DD) | `https://www.eoptolink.com` | *None* (Datasheets gated; available via direct sales inquiry under NDA) | *None* (Public first-party pages list general specifications without an explicit SiPh binding sentence; distributor listings are non-first-party). | **FAIL** (No open-access first-party datasheet URL; unretrievable binding) |
| **InnoLight Technology** | 800G DR8 SiPh Series (e.g. T-OL8CNT-N00) | `https://www.innolight.com` | *None* (Restricted / NDA customer portal only) | *None* (Public site provides high-level portfolio overviews; exact silicon photonics datasheets are customer-gated under NDA). | **FAIL** (Login/NDA gated; no publicly retrievable first-party datasheet) |
| **Hyper Photonix** | HSO6-800-DR-P8S / HSO6-800-LP-P8S | `https://www.hyperphotonix.com/product_detail/1249.html` | *None* (No standalone open-access PDF datasheet hosted) | *None* (Product page text specifies optical/electrical parameters, CMIS, and reach, but contains no sentence binding the specific SKU to SiPh/PIC). | **FAIL** (Missing product-level SiPh binding sentence; branding-only platform claims) |
| **SiFotonics Technologies** | 800G-DR8 Optical Transceiver / Engine | `https://www.sifotonics.com` | *None* (Not publicly indexed / request-gated) | *None* (Silicon photonics transceivers are discussed in press announcements, but no first-party commercial SKU datasheet is published). | **FAIL** (No direct first-party downloadable datasheet URL) |

---

### Detailed Missing Binding Analysis

#### 1. Intel Corporation (800G DR8 / 2x400G FR4 Platform)
- **Document Disconnect:** Intel published Material Declaration Data Sheets (MDDS) for bare silicon component dies (e.g., *800G DR8 Transmitter PIC*, MM# 94814; *800G 2XFR4 Transmitter PIC*, MM# 94811; *800G Receiver PIC*, MM# 94813) and demonstrated transmitter subsystems in conference presentations (e.g., OFC). However, Intel never released an open-access, commercial optical transceiver product datasheet explicitly tying an end-product 800G transceiver SKU to the silicon-photonics PIC.
- **Gate Violations:** Violates **Gate 1** (no complete transceiver datasheet URL), **Gate 2** (material declarations for sub-components and conference demos cannot be inherited by a commercial transceiver SKU), and **Gate 4** (prohibits merging 2xFR4 material declarations, OFC transmitter demos, and partner PR into a synthetic SKU).

#### 2. Jabil Inc. (800G OSFP 2xFR4 Optical Transceiver)
- **Document Disconnect:** Jabil's first-party product documentation (*800G OSFP 2xFR4 Optical Transceiver*) provides electrical, mechanical, and optical specifications (IEEE 800GAUI-4, 2 km reach, 15W power dissipation, dual LC interface), but contains no text identifying the transmitter or PIC implementation as silicon photonics.
- **Gate Violations:** Violates **Gate 2** (corporate statements regarding Jabil's silicon photonics packaging capabilities and partner press releases with Intel/MaxLinear cannot be inherited by the commercial transceiver product page).

#### 3. Cisco Systems, Inc. (Cisco OSFP 800G Transceiver Modules)
- **Document Disconnect:** Cisco’s official *Cisco OSFP 800G Transceiver Modules Data Sheet* covers commercial products (including OSFP-800G-DR8 and OSFP-800G-2FR4). An exhaustive search of the document content confirms that the terms "Silicon Photonics", "SiPh", and "PIC" do not appear anywhere in the text. The document specifies interface parameters and standards conformance while remaining implementation-agnostic.
- **Gate Violations:** Violates **Gate 1** and **Gate 2** (no first-party binding sentence in the product datasheet).

#### 4. Acacia Communications / Cisco (Acacia 800ZR / 800G ZR+)
- **Document Disconnect:** Acacia publishes technical blogs, whitepapers, and press releases discussing the 9th-generation Delphi DSP ASIC and 130+ Gbaud Silicon Photonics (SiPh) PIC technology. However, Acacia does not host an open-access, downloadable commercial product datasheet for an individual 800G SKU that explicitly binds that product to a SiPh PIC.
- **Gate Violations:** Violates **Gate 1** (unretrievable first-party datasheet URL) and **Gate 2** (platform/newsroom architecture claims cannot substitute for product datasheet documentation).

#### 5. Marvell Technology, Inc. (COLORZ 800 Family)
- **Document Disconnect:** Marvell describes the *COLORZ 800* family at a broad portfolio level as integrating the Orion coherent DSP with a silicon photonics platform. However, first-party product collateral URLs return HTTP 403 (access restricted), and no publicly accessible, independent datasheet exists with an explicit SiPh binding sentence for a specific commercial SKU.
- **Gate Violations:** Violates **Gate 1** (no retrievable open-access datasheet), **Gate 2** (family-level platform statement), and **Gate 5** (login/permission-gated content cannot support section-level claims).

#### 6. Coherent Corp. (800G-DR8 / FTCE Transceivers)
- **Document Disconnect:** While Coherent discusses silicon photonics transceivers in corporate engineering articles (contrasting SiPh with InP for specific reach profiles), its published commercial datasheets for 800G client optics (such as the FTCE family) either specify EML/InP transmitters, omit the optical implementation detail, or require restricted customer access.
- **Gate Violations:** Violates **Gate 1** and **Gate 2** (general engineering articles cannot be combined with separate commercial SKU datasheets).

#### 7. Eoptolink Technology Inc. (EOLO-138HG-5H-SM / EOLD-138HG-5H-SM)
- **Document Disconnect:** Third-party distributor summaries (such as i-wave) describe these modules as incorporating a "Silicon Photonics 1310nm transmitter." However, Eoptolink’s own public website provides only high-level summary tables, and full first-party technical datasheets are gated behind direct sales inquiry (`sales@eoptolink.com`) under commercial NDA.
- **Gate Violations:** Violates **Gate 1** (no direct first-party datasheet URL) and **Gate 2** (third-party distributor text cannot serve as first-party binding).

#### 8. InnoLight Technology (800G DR8 SiPh)
- **Document Disconnect:** InnoLight's silicon photonics 800G products (such as the Tower Semiconductor-fabricated SiPh line) are documented only under strict customer NDA and commercial engagement channels. Public web assets provide only high-level marketing briefs without open-access downloadable datasheets.
- **Gate Violations:** Violates **Gate 1**, **Gate 2**, and **Gate 5** (login/NDA gated).

#### 9. Hyper Photonix (HSO6-800-DR-P8S / HSO6-800-LP-P8S)
- **Document Disconnect:** Hyper Photonix utilizes the brand name "Hyper Silicon™" across its website headers and company overview pages. However, the exact first-party product description for the 800G transceiver on its product page (`/product_detail/1249.html`) details optical rate, wavelength, connectors, and IEEE compliance without an explicit sentence binding the product to a silicon-photonics PIC or transmitter. No standalone first-party PDF datasheet is publicly hosted.
- **Gate Violations:** Violates **Gate 1** (no downloadable datasheet URL) and **Gate 2** (corporate branding/platform claims cannot substitute for an explicit product binding sentence).

#### 10. SiFotonics Technologies (800G-DR8)
- **Document Disconnect:** SiFotonics discusses 800G-DR8 silicon photonics optical engines and transceivers in press releases and exhibition summaries, but does not provide an open-access, direct first-party downloadable datasheet URL for an individual commercial SKU.
- **Gate Violations:** Violates **Gate 1** and **Gate 2** (press announcements cannot substitute for first-party product datasheets).
