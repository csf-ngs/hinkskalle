<template>
  <v-expansion-panel v-if="manifest">
    <v-expansion-panel-header>
      <v-row no-gutters justify="space-between">
        <v-col>
          <span v-if="manifest.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip
              color="green lighten-1"
              v-for="tag in manifest.tags" :key="tag"
              @click.stop="copyTag(tag)">
                {{tag}}
            </v-chip>
          </span>
        </v-col>
        <v-col class="d-flex justify-center align-center">
          <span class="font-weight-medium">Filename:</span> {{manifest.filename}}&nbsp;|&nbsp;
          <span class="font-weight-medium">Size:</span> {{manifest.total_size | prettyBytes() }}
        </v-col>
        <v-col class="d-flex justify-end align-center mr-4">
          <div v-if="manifest.type=='singularity'">
            <v-icon>mdi-adjust</v-icon>
            Singularity
          </div>
          <div v-else-if="manifest.type=='docker'">
            <v-icon>mdi-ferry</v-icon>
            Docker
          </div>
          <div v-else-if="manifest.type=='oras'">
            <v-icon>mdi-folder</v-icon>
            ORAS
          </div>
          <div v-else-if="manifest.type=='other'">
            <v-icon>mdi-file-question</v-icon>
            Other/Unknown
          </div>
          <div v-else-if="manifest.type=='invalid'">
            <v-icon color="error">mdi-file-cancel-outline</v-icon>
            Invalid Config
          </div>

        </v-col>
      </v-row>
    </v-expansion-panel-header>
  </v-expansion-panel>
</template>
<script lang="ts">
import { Manifest } from '@/store/models';
import Vue from 'vue';
import { getEnv } from '@/util/env';

export default Vue.extend({
  name: 'ManifestDetails',
  props: {
    manifest: {
      type: Manifest,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data: (): { localState: {} } => ({
    localState: {},
  }),
  computed: {},
  methods: {
    pullCmd(tag: string): string {
      const backend = (getEnv('VUE_APP_BACKEND_URL') as string).replace(/^https?:\/\//, '');
      const hasHttps = (getEnv('VUE_APP_BACKEND_URL') as string).startsWith('https');
      const path = `${this.manifest.entityName}/${this.manifest.collectionName}/${this.manifest.containerName}:${tag}`
      switch(this.manifest.type) {
        case('singularity'):
          return `singularity pull oras://${backend}${path}`
        case('docker'):
          return `docker pull ${backend}${path}`
        case('oras'):
          return `oras pull ${hasHttps ? '' : '--plain-http '}${backend}${path}`
        default:
          return `curl something`
      }
    },
    copyTag(tag: string) {
      this.$copyText(this.pullCmd(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard"))

    }
  },
});
</script>