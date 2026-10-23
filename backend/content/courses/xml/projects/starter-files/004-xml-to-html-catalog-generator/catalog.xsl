<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8"/>
  <xsl:template match="/catalog">
    <html><head><title>Product catalog</title></head><body><h1>Product catalog</h1><ul>
      <xsl:for-each select="product"><li><xsl:value-of select="name"/> — <xsl:value-of select="price"/></li></xsl:for-each>
    </ul></body></html>
  </xsl:template>
</xsl:stylesheet>
