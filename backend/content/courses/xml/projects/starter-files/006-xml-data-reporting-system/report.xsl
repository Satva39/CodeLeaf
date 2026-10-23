<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"><xsl:output method="text"/><xsl:template match="/sales"><xsl:for-each select="sale"><xsl:value-of select="product"/><xsl:text> quantity=</xsl:text><xsl:value-of select="quantity"/><xsl:text>&#10;</xsl:text></xsl:for-each></xsl:template></xsl:stylesheet>
