<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:c="https://example.org/catalog" exclude-result-prefixes="c">
  <xsl:output method="html" encoding="UTF-8"/>
  <xsl:template match="/c:catalog"><html><head><title>Catalog</title></head><body><h1>Catalog</h1><ul><xsl:for-each select="c:product"><li><xsl:value-of select="c:name"/> — <xsl:value-of select="c:price"/></li></xsl:for-each></ul></body></html></xsl:template>
</xsl:stylesheet>
