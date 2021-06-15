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
          <span v-if="manifest.filename!=='(none)'">
            <span class="font-weight-medium">Filename:</span> {{manifest.filename}}&nbsp;|&nbsp;
          </span>
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
    <v-expansion-panel-content v-if="manifest.type=='docker'">
      <docker-details :manifest="manifest"></docker-details>
      
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>
<script lang="ts">
import { Manifest } from '@/store/models';
import DockerDetails from '@/components/DockerDetails.vue';
import Vue from 'vue';

export default Vue.extend({
  components: { DockerDetails },
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
    copyTag(tag: string) {
      this.$copyText(this.manifest.pullCmd(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard"))
    }
  },
});
</script>